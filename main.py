from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

import dictionary

app = FastAPI(
    title="Glossamer",
    description="✨ Just-right contextual definitions to keep the reader focused on the passage",
    version="0.1.0",
)

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.get("/define/{word}")
def define(word: Annotated[str, Path(max_length=100)]):
    if not word.strip():
        raise HTTPException(422, "Word must not be empty")
    result = dictionary.define(word)
    if result is None:
        raise HTTPException(404, f"No definition found for {word.strip()!r}")
    return result
