import sys
import types

# stub the embedder so tests never download or load the real model
_stub = types.ModuleType("app.retrieval.embedder")
_stub.embed = lambda texts: [[0.0, 0.0, 0.0] for _ in texts]
sys.modules["app.retrieval.embedder"] = _stub

from app.retrieval.bm25 import tokenize  # noqa: E402
from app.retrieval.search import cap_per_file, rrf_merge  # noqa: E402


def chunk(path: str, line: int = 1) -> dict:
    return {"path": path, "start_line": line}


def test_rrf_ranks_chunk_found_by_both_retrievers_first():
    a, b, c = chunk("a.py"), chunk("b.py"), chunk("c.py")
    merged = rrf_merge([[b, a], [c, a]])
    assert merged[0] == a
    assert {m["path"] for m in merged} == {"a.py", "b.py", "c.py"}


def test_rrf_weight_favors_heavier_ranking():
    a, b = chunk("a.py"), chunk("b.py")
    assert rrf_merge([[a], [b]], [2.0, 1.0])[0] == a
    assert rrf_merge([[a], [b]], [1.0, 2.0])[0] == b


def test_cap_per_file_limits_chunks_per_path():
    chunks = [chunk("a.py", i) for i in range(5)] + [chunk("b.py")]
    out = cap_per_file(chunks, 2)
    assert [c["path"] for c in out] == ["a.py", "a.py", "b.py"]


def test_tokenize_splits_identifiers():
    assert tokenize("fixed_window.lua") == ["fixed", "window", "lua"]
    assert tokenize("getUserName") == ["get", "user", "name"]