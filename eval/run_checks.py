import json
import sys
import time

from google.genai.errors import ServerError

from app.llm.answer import answer_question

NEGATIVE = [
    "Which file implements the leaky bucket algorithm?",
    "How does the service expose Prometheus metrics?",
    "Which database stores the request logs for analytics?",
]
POSITIVE = [("Which file defines the POST /check route?", "app/main.py")]


def ask(repo_id: str, q: str, tries: int = 4) -> dict:
    for attempt in range(tries):
        try:
            return answer_question(repo_id, q)
        except ServerError:
            if attempt == tries - 1:
                raise
            wait = 5 * 2**attempt  # 5s, 10s, 20s
            print(f"  503, retrying in {wait}s...")
            time.sleep(wait)


def run(repo_id: str) -> None:
    for q in NEGATIVE:
        res = ask(repo_id, q)
        ok = not res["sources"]  # a correct refusal should cite nothing
        print(f"{'PASS' if ok else 'CHECK'} [negative] {q}")
        print("  answer :", res["answer"][:300].replace("\n", " "))
        print("  sources:", [s["path"] for s in res["sources"]], "\n")

    for q, expected in POSITIVE:
        res = ask(repo_id, q)
        ok = any(s["path"] == expected for s in res["sources"])
        print(f"{'PASS' if ok else 'FAIL'} [positive] {q}")
        print("  answer :", res["answer"][:300].replace("\n", " "))
        print("  sources:", [s["path"] for s in res["sources"]], "\n")


if __name__ == "__main__":
    run(sys.argv[1])