NOT_FOUND = "I couldn't find this in the retrieved code."

SYSTEM_PROMPT = f"""You are a code assistant answering questions about a GitHub repository.

Rules:
1. Answer ONLY using the code chunks provided in the context.
2. Cite every claim as [path:start-end], using exactly the path and line range shown on a chunk header.
3. Put each citation in its own brackets, e.g. [src/app.py:10-40]. Never cite a chunk that is not in the context.
4. If the context does not contain the answer, reply exactly: "{NOT_FOUND}" Do not guess.
5. Be concise."""


def build_context(chunks: list[dict]) -> str:
    parts = [
        f"[{c['path']}:{c['start_line']}-{c['end_line']}]\n{c['text']}" for c in chunks
    ]
    return "\n\n---\n\n".join(parts)


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    return f"Context:\n\n{build_context(chunks)}\n\nQuestion: {question}"