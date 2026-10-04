import json, sys
from app.retrieval.search import search_scored

repo_id = sys.argv[1]
qs = json.load(open("eval/questions.json", encoding="utf-8"))
groups = {"answerable": [], "refuse": []}
for q in qs:
    g = "answerable" if q["kind"] in ("easy", "multi") else "refuse"
    groups[g].append((search_scored(repo_id, q["q"])[1], q["q"]))

for g, rows in groups.items():
    rows.sort()
    s = [r[0] for r in rows]
    print(f"{g:11} n={len(s):2}  min={s[0]:.3f}  median={s[len(s)//2]:.3f}  max={s[-1]:.3f}")
print("\nlowest 5 answerable:")
for sc, q in groups["answerable"][:5]:
    print(f"  {sc:.3f}  {q}")