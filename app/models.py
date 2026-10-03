from typing import Literal

from pydantic import BaseModel, Field


class RepoCreate(BaseModel):
    url: str


class RepoStatus(BaseModel):
    id: str
    url: str
    status: str
    chunk_count: int
    error: str | None = None


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=6)