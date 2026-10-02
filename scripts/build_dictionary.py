"""Export WordNet into data/dictionary.db for the /define endpoint.

Dev-only: requires nltk (`uv sync`), never imported by the deployed app.
Run with: uv run scripts/build_dictionary.py
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import nltk

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dictionary.db"

# NLTK's lemma index stores adjectives under "a" (satellites included) and
# duplicates them under "s", so "s" is skipped to avoid double rows.
POS_LIST = ["n", "v", "a", "r"]


def main() -> None:
    with tempfile.TemporaryDirectory() as nltk_dir:
        nltk.download("wordnet", download_dir=nltk_dir, quiet=True)
        nltk.data.path.insert(0, nltk_dir)
        from nltk.corpus import wordnet as wn

        wn.ensure_loaded()
        build(wn)

    print(f"Wrote {DB_PATH} ({DB_PATH.stat().st_size / 1_000_000:.1f} MB)")


def build(wn) -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE entries (
            word TEXT NOT NULL,
            sense_order INTEGER NOT NULL,
            pos TEXT NOT NULL,
            definition TEXT NOT NULL,
            examples TEXT NOT NULL,  -- JSON array
            synonyms TEXT NOT NULL   -- JSON array
        );
        CREATE TABLE exceptions (
            inflected TEXT NOT NULL,
            pos TEXT NOT NULL,
            base TEXT NOT NULL
        );
        """
    )

    rows = []
    for word in sorted(wn.all_lemma_names()):
        sense_order = 0
        for pos in POS_LIST:
            for offset in wn._lemma_pos_offset_map[word].get(pos, []):
                synset = wn.synset_from_pos_and_offset(pos, offset)
                synonyms = [
                    name.replace("_", " ")
                    for name in synset.lemma_names()
                    if name.lower() != word
                ]
                rows.append(
                    (
                        word,
                        sense_order,
                        synset.pos(),
                        synset.definition(),
                        json.dumps(synset.examples()),
                        json.dumps(synonyms),
                    )
                )
                sense_order += 1
    db.executemany("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?)", rows)

    exceptions = [
        (inflected, pos, base)
        for pos in POS_LIST
        for inflected, bases in wn._exception_map[pos].items()
        for base in bases
    ]
    db.executemany("INSERT INTO exceptions VALUES (?, ?, ?)", exceptions)

    db.executescript(
        """
        CREATE INDEX entries_word ON entries (word, sense_order);
        CREATE INDEX exceptions_inflected ON exceptions (inflected);
        """
    )
    db.commit()
    db.execute("VACUUM")
    db.close()
    print(f"{len(rows):,} entries, {len(exceptions):,} exceptions")


if __name__ == "__main__":
    main()
