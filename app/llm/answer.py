import re

from app.llm.client import get_llm
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.retrieval.store import query

CITATION = re.compile(r"\[([^\[\]]+?):(\d+)-(\d+)\]")


def answer_question(repo_id: str, question: str, k: int = 5) -> dict:
    chunks = query(repo_id, question, k)
    text = get_llm().complete(SYSTEM_PROMPT, build_user_prompt(question, chunks))

    by_range = {(c["path"], c["start_line"], c["end_line"]): c for c in chunks}
    sources, seen = [], set()
    for path, start, end in CITATION.findall(text):
        key = (path, int(start), int(end))
        if key in by_range and key not in seen:
            seen.add(key)
            sources.append(
                {"path": path, "start": key[1], "end": key[2], "snippet": by_range[key]["text"][:300]}
            )
    return {"answer": text, "sources": sources}