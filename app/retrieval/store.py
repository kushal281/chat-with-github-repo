import chromadb

from app.config import settings
from app.ingest.chunker import Chunk
from app.retrieval.embedder import embed

_client = chromadb.PersistentClient(path=settings.chroma_dir)
_collection = _client.get_or_create_collection(
    "chunks", metadata={"hnsw:space": "cosine"}
)

BATCH = 64


def add_chunks(repo_id: str, chunks: list[Chunk]) -> int:
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        _collection.upsert(
            ids=[f"{repo_id}:{c.path}:{c.start_line}" for c in batch],
            embeddings=embed([c.embed_text for c in batch]),
            documents=[c.text for c in batch],
            metadatas=[
                {
                    "repo_id": repo_id,
                    "path": c.path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                }
                for c in batch
            ],
        )
    return len(chunks)


def query(repo_id: str, question: str, k: int = 5) -> list[dict]:
    res = _collection.query(
        query_embeddings=embed([question]),
        n_results=k,
        where={"repo_id": repo_id},
    )
    return [
        {
            "path": m["path"],
            "start_line": m["start_line"],
            "end_line": m["end_line"],
            "text": doc,
            "distance": dist,
        }
        for m, doc, dist in zip(
            res["metadatas"][0], res["documents"][0], res["distances"][0]
        )
    ]


def delete_repo(repo_id: str) -> None:
    _collection.delete(where={"repo_id": repo_id})