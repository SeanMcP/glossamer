# glossamer

✨ Just-right contextual definitions to keep the reader focused on the passage

## Dictionary data

`GET /define/{word}` reads WordNet from `data/dictionary.db`, a committed SQLite file. NLTK is a dev-only dependency and is never imported at runtime.

To regenerate the database:

```sh
uv sync                              # installs dev deps (nltk, pytest)
uv run scripts/build_dictionary.py   # downloads WordNet to a temp dir, rebuilds the db
uv run pytest
```
