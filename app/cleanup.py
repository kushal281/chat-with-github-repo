import sqlite3
import time
from contextlib import closing

from app.config import settings
from app.retrieval.bm25 import invalidate
from app.retrieval.store import delete_repo


def _run(sql: str, params: tuple = ()) -> list:
    with closing(sqlite3.connect(settings.db_path)) as c, c:
        return c.execute(sql, params).fetchall()


def ensure_columns() -> None:
    cols = [r[1] for r in _run("pragma table_info(repos)")]
    if "last_used_at" not in cols:
        _run("alter table repos add column last_used_at REAL")
        _run("update repos set last_used_at = ?", (time.time(),))


def touch(repo_id: str) -> None:
    _run("update repos set last_used_at = ? where id = ?", (time.time(), repo_id))


def _norm(url: str) -> str:
    return url.strip().rstrip("/").removesuffix(".git").lower()


def find_existing(url: str) -> str | None:
    for repo_id, u in _run("select id, url from repos where status != 'failed'"):
        if _norm(u) == _norm(url):
            return repo_id
    return None


def remove_repo_fully(repo_id: str) -> None:
    delete_repo(repo_id)  # Chroma
    invalidate(repo_id)   # BM25 cache in RAM
    _run("delete from repos where id = ?", (repo_id,))


def purge() -> None:
    # only ready/failed repos are touched; ones still ingesting are left alone
    done = "status in ('ready', 'failed')"
    if settings.repo_ttl_hours:
        cutoff = time.time() - settings.repo_ttl_hours * 3600
        stale = _run(
            f"select id from repos where {done} and coalesce(last_used_at, 0) < ?",
            (cutoff,),
        )
        for (repo_id,) in stale:
            remove_repo_fully(repo_id)
    if settings.max_repos:
        rows = _run(
            f"select id from repos where {done} order by coalesce(last_used_at, 0) desc"
        )
        for (repo_id,) in rows[settings.max_repos:]:
            remove_repo_fully(repo_id)