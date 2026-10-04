from app.retrieval.bm25 import bm25_query
from app.retrieval.store import query

RRF_K = 60
POOL = 20  # candidates taken from each retriever before merging


def rrf_merge(rankings: list[list[dict]], weights: list[float] | None = None) -> list[dict]:
    weights = weights or [1.0] * len(rankings)
    scores: dict[tuple, float] = {}
    chunks: dict[tuple, dict] = {}
    for w, ranking in zip(weights, rankings):
        for rank, c in enumerate(ranking):
            key = (c["path"], c["start_line"])
            chunks[key] = c
            scores[key] = scores.get(key, 0.0) + w / (RRF_K + rank + 1)
    return [chunks[key] for key in sorted(scores, key=scores.get, reverse=True)]


def cap_per_file(chunks: list[dict], max_per_file: int) -> list[dict]:
    counts: dict[str, int] = {}
    out = []
    for c in chunks:
        if counts.get(c["path"], 0) < max_per_file:
            counts[c["path"]] = counts.get(c["path"], 0) + 1
            out.append(c)
    return out


def search_scored(repo_id: str, question: str, k: int = 5, mode: str = "hybrid",
                  max_per_file: int | None = None, vec_weight: float = 1.0) -> tuple[list[dict], float]:
    vec = query(repo_id, question, POOL)
    best = 1 - vec[0]["distance"] / 2 if vec else 0.0
    if mode == "vector":
        merged = vec
    else:
        merged = rrf_merge([vec, bm25_query(repo_id, question, POOL)], [vec_weight, 1.0])
    if max_per_file:
        merged = cap_per_file(merged, max_per_file)
    return merged[:k], best


def search(*args, **kwargs) -> list[dict]:
    return search_scored(*args, **kwargs)[0]  # eval and tests keep working unchanged