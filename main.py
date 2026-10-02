from fastapi import FastAPI

app = FastAPI(
    title="Glossamer",
    description="✨ Just-right contextual definitions to keep the reader focused on the passage",
    version="0.1.0",
)

@app.get("/ping")
async def ping():
    return {"message": "pong"}