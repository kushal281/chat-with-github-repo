import subprocess

from app.db import update_repo
from app.ingest.chunker import chunk_file
from app.ingest.fetch import cleanup, clone_repo
from app.ingest.filters import iter_code_files
from app.retrieval.store import add_chunks


def run_ingestion(repo_id: str, url: str) -> None:
    root = None
    try:
        root = clone_repo(url)
        update_repo(repo_id, status="indexing")
        chunks = [c for f in iter_code_files(root) for c in chunk_file(root, f)]
        if not chunks:
            raise ValueError("No indexable files found")
        n = add_chunks(repo_id, chunks)
        update_repo(repo_id, status="ready", chunk_count=n)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or b"").decode(errors="ignore")[-300:]
        update_repo(repo_id, status="failed", error=f"git clone failed: {stderr}")
    except subprocess.TimeoutExpired:
        update_repo(repo_id, status="failed", error="git clone timed out")
    except Exception as e:
        update_repo(repo_id, status="failed", error=str(e)[:300])
    finally:
        if root:
            cleanup(root)