import sqlite3
import uuid

from app.config import settings


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS repos (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                error TEXT
            )"""
        )


def create_repo(url: str) -> str:
    repo_id = uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute(
            "INSERT INTO repos (id, url, status) VALUES (?, ?, 'cloning')",
            (repo_id, url),
        )
    return repo_id


def update_repo(repo_id: str, **fields) -> None:
    cols = ", ".join(f"{k} = ?" for k in fields)  # keys come from our code, never from users
    with _conn() as c:
        c.execute(f"UPDATE repos SET {cols} WHERE id = ?", (*fields.values(), repo_id))


def get_repo(repo_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM repos WHERE id = ?", (repo_id,)).fetchone()
    return dict(row) if row else None