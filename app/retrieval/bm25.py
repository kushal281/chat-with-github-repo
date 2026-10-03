import re

from rank_bm25 import BM25Okapi

from app.retrieval.store import _collection

# repo_id -> (bm25 index, chunks)
_indexes: dict[str, tuple[BM25Okapi, list[dict]]] = {}


def tokenize(text: str) -> list[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [t.lower() for t in re.findall(r"[A-Za-z0-9]+", text)]


def _build(repo_id: str) -> tuple[BM25Okapi, list[dict]]:
    res = _collection.get(
        where={"repo_id": repo_id}, include=["documents", "metadatas"]
    )
    chunks = [
        {
            "path": m["path"],
            "start_line": m["start_line"],
            "end_line": m["end_line"],
            "text": doc,
        }
        for m, doc in zip(res["metadatas"], res["documents"])
    ]
    corpus = [tokenize(c["path"] + " " + c["text"]) for c in chunks]
    return BM25Okapi(corpus), chunks


def bm25_query(repo_id: str, question: str, k: int = 20) -> list[dict]:
    if repo_id not in _indexes:
        _indexes[repo_id] = _build(repo_id)
    bm25, chunks = _indexes[repo_id]
    scores = bm25.get_scores(tokenize(question))
    top = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:k]
    return [chunks[i] for i in top if scores[i] > 0]


def invalidate(repo_id: str) -> None:
    _indexes.pop(repo_id, None)