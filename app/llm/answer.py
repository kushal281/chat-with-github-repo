import re

from app.llm.client import get_llm
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.retrieval.store import query

CITATION = re.compile(r"\[([^\[\]]+?):(\d+)-(\d+)\]")


def _find_chunk(chunks, path, start, end):
    return next(
        (c for c in chunks
         if c["path"] == path and c["start_line"] <= start <= end <= c["end_line"]),
        None,
    )


def answer_question(repo_id: str, question: str, k: int = 5) -> dict:
    chunks = query(repo_id, question, k)
    text = get_llm().complete(SYSTEM_PROMPT, build_user_prompt(question, chunks))
    sources, ids = [], {}

    def number_citation(m):
        path, start, end = m.group(1), int(m.group(2)), int(m.group(3))
        key = (path, start, end)
        if key not in ids:
            chunk = _find_chunk(chunks, path, start, end)
            if chunk is None:
                return ""  # citation not backed by a retrieved chunk: drop it
            lines = chunk["text"].splitlines()
            off = chunk["start_line"]
            snippet = "\n".join(lines[start - off : end - off + 1])[:600]
            ids[key] = len(sources) + 1
            sources.append(
                {"id": ids[key], "path": path, "start": start, "end": end, "snippet": snippet}
            )
        return f"[{ids[key]}]"

    return {"answer": CITATION.sub(number_citation, text), "sources": sources}