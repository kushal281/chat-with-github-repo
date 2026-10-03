from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.config import settings
from app.db import create_repo, get_repo, init_db
from app.ingest.fetch import parse_repo_url
from app.ingest.pipeline import run_ingestion
from app.models import RepoCreate, RepoStatus
from app.llm.answer import answer_question
from app.models import ChatRequest, RepoCreate, RepoStatus
from app.cleanup import ensure_columns, find_existing, purge, remove_repo_fully, touch
import logging


logger = logging.getLogger("uvicorn.error")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_columns()
    purge()
    yield


app = FastAPI(title="Repo Chat", lifespan=lifespan)


@app.get("/")
def index():
    return FileResponse(FRONTEND)


@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": bool(settings.llm_api_key)}


@app.post("/repos", status_code=202)
def add_repo(body: RepoCreate, background: BackgroundTasks):
    try:
        parse_repo_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    existing = find_existing(body.url)
    if existing:
        touch(existing)
        return {"repo_id": existing}
    purge()
    repo_id = create_repo(body.url)
    touch(repo_id)
    background.add_task(run_ingestion, repo_id, body.url)
    return {"repo_id": repo_id}


@app.get("/repos/{repo_id}", response_model=RepoStatus)
def repo_status(repo_id: str):
    repo = get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo


@app.post("/repos/{repo_id}/chat")
def chat(repo_id: str, body: ChatRequest):
    repo = get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    if repo["status"] != "ready":
        raise HTTPException(status_code=409, detail=f"Repo is {repo['status']}")
    touch(repo_id)
    try:
        return answer_question(
            repo_id, body.question, [t.model_dump() for t in body.history]
        )
    except Exception:
        logger.exception("LLM request failed")
        raise HTTPException(status_code=502, detail="LLM request failed")


@app.delete("/repos/{repo_id}")
def remove_repo(repo_id: str):
    if not get_repo(repo_id):
        raise HTTPException(status_code=404, detail="Repo not found")
    remove_repo_fully(repo_id)
    return {"deleted": repo_id}