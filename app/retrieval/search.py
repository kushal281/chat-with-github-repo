from app.retrieval.bm25 import bm25_query
from app.retrieval.store import query

RRF_K = 60
POOL = 20  # candidates taken from each retriever before merging


def rrf_merge(rankings: list[list[dict]]) -> list[dict]:
    """Reciprocal Rank Fusion: score = sum(1 / (60 + rank)) across rankings."""
    scores: dict[tuple, float] = {}
    chunks: dict[tuple, dict] = {}
    for ranking in rankings:
        for rank, c in enumerate(ranking):
            key = (c["path"], c["start_line"])
            chunks[key] = c
            scores[key] = scores.get(key, 0.0) + 1 / (RRF_K + rank + 1)
    return [chunks[key] for key in sorted(scores, key=scores.get, reverse=True)]


def cap_per_file(chunks: list[dict], max_per_file: int) -> list[dict]:
    counts: dict[str, int] = {}
    out = []
    for c in chunks:
        if counts.get(c["path"], 0) < max_per_file:
            counts[c["path"]] = counts.get(c["path"], 0) + 1
            out.append(c)
    return out


def search(
    repo_id: str,
    question: str,
    k: int = 5,
    mode: str = "hybrid",
    max_per_file: int | None = None,
) -> list[dict]:
    vec = query(repo_id, question, POOL)
    if mode == "vector":
        merged = vec
    else:
        merged = rrf_merge([vec, bm25_query(repo_id, question, POOL)])
    if max_per_file:
        merged = cap_per_file(merged, max_per_file)
    return merged[:k]