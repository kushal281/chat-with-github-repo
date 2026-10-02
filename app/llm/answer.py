import re

from app.llm.client import get_llm
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.retrieval.store import query

CITATION = re.compile(r"\[([^\[\]]+?):(\d+)(?:-(\d+))?\]")
MERGE_GAP = 3


def _line_maps(chunks: list[dict]) -> dict[str, dict[int, str]]:
    maps: dict[str, dict[int, str]] = {}
    for c in chunks:
        m = maps.setdefault(c["path"], {})
        for i, line in enumerate(c["text"].splitlines()):
            m[c["start_line"] + i] = line
    return maps


def _parse(m: re.Match) -> tuple[str, int, int]:
    start = int(m.group(2))
    return m.group(1), start, int(m.group(3) or start)


def answer_question(repo_id: str, question: str, k: int = 5) -> dict:
    chunks = query(repo_id, question, k)
    text = get_llm().complete(SYSTEM_PROMPT, build_user_prompt(question, chunks))
    maps = _line_maps(chunks)

    # 1. keep only citations whose every line was actually retrieved
    valid = set()
    for m in CITATION.finditer(text):
        path, start, end = _parse(m)
        lm = maps.get(path)
        if lm and start <= end and all(l in lm for l in range(start, end + 1)):
            valid.add((path, start, end))

    # 2. merge overlapping or nearby ranges within each file
    merged: dict[str, list[list[int]]] = {}
    for path, start, end in sorted(valid):
        ranges = merged.setdefault(path, [])
        if ranges and start <= ranges[-1][1] + MERGE_GAP:
            ranges[-1][1] = max(ranges[-1][1], end)
        else:
            ranges.append([start, end])

    # 3. number sources by first appearance and rewrite citations as [n]
    sources: list[dict] = []
    ids: dict[tuple, int] = {}

    def rewrite(m: re.Match) -> str:
        path, start, end = _parse(m)
        if (path, start, end) not in valid:
            return ""
        s, e = next((a, b) for a, b in merged[path] if a <= start and end <= b)
        key = (path, s, e)
        if key not in ids:
            ids[key] = len(sources) + 1
            snippet = "\n".join(maps[path].get(l, "") for l in range(s, e + 1))[:800]
            sources.append({"id": ids[key], "path": path, "start": s, "end": e, "snippet": snippet})
        return f"[{ids[key]}]"

    out = CITATION.sub(rewrite, text)
    out = re.sub(r"(\[(\d+)\])(?:\s*\[\2\])+", r"\1", out)  # [1] [1] -> [1]
    return {"answer": out, "sources": sources}