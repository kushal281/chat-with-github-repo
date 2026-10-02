from pydantic import BaseModel


class RepoCreate(BaseModel):
    url: str


class RepoStatus(BaseModel):
    id: str
    url: str
    status: str
    chunk_count: int
    error: str | None = None