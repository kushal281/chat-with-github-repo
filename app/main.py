from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Repo Chat")


@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": bool(settings.llm_api_key)}