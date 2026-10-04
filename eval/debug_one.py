import sys
from app.llm.client import get_llm
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.retrieval.search import search_scored
import re

repo_id, q = sys.argv[1], sys.argv[2]
chunks, best = search_scored(repo_id, q, 5, mode="hybrid", max_per_file=2, vec_weight=2.0)
print("best:", round(best, 3))
for c in chunks:
    print("  chunk", c["path"], c["start_line"], c["end_line"])
    
llm = get_llm()
for i in range(8):
    out = llm.complete(SYSTEM_PROMPT, build_user_prompt(q, chunks, []))
    print(i, "CITED" if re.search(r"\[[^\[\]]+:\d+", out) else "NO CITATION", "|", out[:90].replace("\n", " "))