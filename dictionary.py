"""WordNet lookups against data/dictionary.db, with no NLTK at runtime.

Lemmatization mirrors NLTK's wn.synsets(): for each part of speech, check the
exception lists, otherwise apply morphy's suffix rules, and keep candidates
that exist in the dictionary.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "dictionary.db"

db = sqlite3.connect(
    f"file:{DB_PATH}?mode=ro&immutable=1", uri=True, check_same_thread=False
)

POS_NAMES = {"n": "noun", "v": "verb", "a": "adjective", "s": "adjective", "r": "adverb"}

# Satellite adjectives ("s") are looked up as adjectives, as in WordNet's index.
POS_CODES = {"n": ("n",), "v": ("v",), "a": ("a", "s"), "r": ("r",)}

# Ported from nltk.corpus.reader.wordnet.WordNetCorpusReader.MORPHOLOGICAL_SUBSTITUTIONS
SUBSTITUTIONS = {
    "n": [("s", ""), ("ses", "s"), ("ves", "f"), ("xes", "x"), ("zes", "z"),
          ("ches", "ch"), ("shes", "sh"), ("men", "man"), ("ies", "y")],
    "v": [("s", ""), ("ies", "y"), ("es", "e"), ("es", ""), ("ed", "e"),
          ("ed", ""), ("ing", "e"), ("ing", "")],
    "a": [("er", ""), ("est", ""), ("er", "e"), ("est", "e")],
    "r": [],
}


def normalize(query: str) -> str:
    return "_".join(query.lower().split())


def define(query: str) -> dict | None:
    word = normalize(query)
    matches = [(form, pos) for pos in POS_CODES for form in _morphy(word, pos)]
    if not matches:
        return None

    # Group senses by word, exact match first, then in order of discovery.
    words = sorted(dict.fromkeys(form for form, _ in matches), key=lambda w: w != word)
    senses, seen = [], set()
    for form in words:
        codes = [code for f, pos in matches if f == form for code in POS_CODES[pos]]
        for pos, definition, examples, synonyms in _senses(form, codes):
            if (pos, definition) in seen:
                continue
            seen.add((pos, definition))
            senses.append({
                "word": form,
                "pos": POS_NAMES[pos],
                "definition": definition,
                "examples": json.loads(examples),
                "synonyms": json.loads(synonyms),
            })
    return {"query": query, "words": words, "senses": senses}


def _morphy(form: str, pos: str) -> list[str]:
    """Port of NLTK's WordNetCorpusReader._morphy."""
    bases = [
        base for (base,) in db.execute(
            "SELECT base FROM exceptions WHERE inflected = ? AND pos = ?", (form, pos)
        )
    ]
    if not bases:
        bases = [form[: -len(old)] + new for old, new in SUBSTITUTIONS[pos] if form.endswith(old)]
    return [
        candidate for candidate in dict.fromkeys([form, *bases])
        if _exists(candidate, POS_CODES[pos])
    ]


def _exists(word: str, codes: tuple[str, ...]) -> bool:
    placeholders = ",".join("?" * len(codes))
    row = db.execute(
        f"SELECT 1 FROM entries WHERE word = ? AND pos IN ({placeholders}) LIMIT 1",
        (word, *codes),
    ).fetchone()
    return row is not None


def _senses(word: str, codes: list[str]) -> list[tuple]:
    placeholders = ",".join("?" * len(codes))
    return db.execute(
        "SELECT pos, definition, examples, synonyms FROM entries "
        f"WHERE word = ? AND pos IN ({placeholders}) ORDER BY sense_order",
        (word, *codes),
    ).fetchall()
