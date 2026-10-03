import json
import sys
from collections import defaultdict
from pathlib import Path

from app.retrieval.store import _collection, query

K = 5
QUESTIONS = Path(__file__).parent / "questions.json"


def norm(path: str) -> str:
    return path.replace("\\", "/")


def retrieve(repo_id: str, question: str, k: int) -> list[dict]:
    return query(repo_id, question, k)


def is_hit(chunks: list[dict], expected: set[str]) -> bool:
    return any(norm(c["path"]) in expected for c in chunks)


def indexed_paths(repo_id: str) -> set[str]:
    res = _collection.get(where={"repo_id": repo_id}, include=["metadatas"])
    return {norm(m["path"]) for m in res["metadatas"]}


def main(repo_id: str) -> None:
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    scored = [i for i in items if i["expected"]]  # skip unanswerable ones

    wanted = {norm(e) for i in scored for e in i["expected"]}
    missing = sorted(wanted - indexed_paths(repo_id))
    if missing:
        print("WARNING, expected files not in index:", missing, "\n")

    hits = {1: 0, 3: 0, K: 0}
    by_kind = defaultdict(lambda: [0, 0])  # kind -> [hits@K, total]
    for item in scored:
        expected = {norm(e) for e in item["expected"]}
        chunks = retrieve(repo_id, item["q"], K)
        for k in hits:
            hits[k] += is_hit(chunks[:k], expected)
        ok = is_hit(chunks, expected)
        by_kind[item["kind"]][0] += ok
        by_kind[item["kind"]][1] += 1
        print(("HIT  " if ok else "MISS ") + item["q"])
        if not ok:
            print("     got:", [norm(c["path"]) for c in chunks])

    n = len(scored)
    print()
    for k, h in hits.items():
        print(f"hit@{k}: {h}/{n} = {h / n:.0%}")
    for kind, (h, t) in by_kind.items():
        print(f"hit@{K} [{kind}]: {h}/{t} = {h / t:.0%}")


if __name__ == "__main__":
    main(sys.argv[1])