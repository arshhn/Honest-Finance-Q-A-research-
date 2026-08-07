"""Day-1 step 9 pilot: 10 seeded questions x sonnet-5, end-to-end.

Produces results/pilot.csv (question, answer, confidence, grade) and
results/pilot_curve.png, and prints an audit table for step 10.
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from api_lib import run_sync
from grade_lib import gold_is_numeric, numeric_grade, parse_response
from prompts import GRADER_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[1]

pilot_ids = set((ROOT / "data" / "pilot_ids.txt").read_text().split())
fb = pd.read_csv(ROOT / "data" / "financebench.csv").set_index("financebench_id")

reqs = []
for line in open(ROOT / "results" / "batch_requests" / "fb_all.jsonl", encoding="utf-8"):
    r = json.loads(line)
    iid = r["custom_id"]  # fb-XXXXX-setting--model
    qid_digits = iid.split("-")[1]
    if f"financebench_id_{qid_digits}" in pilot_ids and iid.endswith("-oracle--sonnet"):
        reqs.append(r)
assert len(reqs) == 10, f"expected 10 pilot requests, got {len(reqs)}"

print("running 10 pilot calls (sonnet-5, oracle evidence)...")
results = run_sync(reqs, workers=5)

rows = []
for r in reqs:
    cid = r["custom_id"]
    fid = "financebench_id_" + cid.split("-")[1]
    meta = fb.loc[fid]
    res = results[cid]
    answer, conf, refused, parse_ok = parse_response(res["text"])
    rows.append({
        "custom_id": cid, "financebench_id": fid, "model_snapshot": res["model"],
        "question": meta.question, "gold": meta.answer,
        "raw_text": res["text"], "answer": answer, "confidence": conf,
        "refused": refused, "parse_ok": parse_ok, "stop_reason": res["stop_reason"],
    })
df = pd.DataFrame(rows)

# grade: numeric via parser, text via sonnet grader
grades, scale_errs, methods = [], [], []
grader_reqs = []
for i, row in df.iterrows():
    if row.refused:
        grades.append("refused"); scale_errs.append(False); methods.append("refusal")
    elif gold_is_numeric(row.gold):
        v, se = numeric_grade(row.gold, row.answer, row.question)
        grades.append(v); scale_errs.append(se); methods.append("numeric_parser")
    else:
        grades.append(None); scale_errs.append(False); methods.append("ai_grader")
        grader_reqs.append({
            "custom_id": f"grade-{i}",
            "params": {"model": "claude-sonnet-5", "max_tokens": 2000,
                       "messages": [{"role": "user", "content": GRADER_PROMPT.format(
                           question=row.question, gold=row.gold, candidate=row.answer)}]},
        })
if grader_reqs:
    print(f"grading {len(grader_reqs)} text answers with sonnet grader...")
    gres = run_sync(grader_reqs, workers=5)
    for req in grader_reqs:
        i = int(req["custom_id"].split("-")[1])
        verdict = gres[req["custom_id"]]["text"].strip().upper()
        grades[i] = {"CORRECT": "correct", "INCORRECT": "incorrect", "REFUSED": "refused"}.get(verdict, f"?{verdict[:20]}")

df["grade"], df["scale_error"], df["grade_method"] = grades, scale_errs, methods
df.to_csv(ROOT / "results" / "pilot.csv", index=False)

# mini risk-coverage curve (M1 verbalized confidence)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = df[~df.refused & df.confidence.notna()].sort_values("confidence", ascending=False)
n_total = len(df)
xs, ys = [], []
for t in sorted(d.confidence.unique(), reverse=True):
    sel = d[d.confidence >= t]
    xs.append(len(sel) / n_total)
    ys.append((sel.grade != "correct").mean())
plt.figure(figsize=(5, 4))
plt.plot(xs, ys, "o-")
plt.xlabel("coverage (fraction answered)"); plt.ylabel("risk (error among answered)")
plt.title("Pilot mini risk-coverage (10 Q, sonnet-5, M1)")
plt.grid(alpha=0.3); plt.tight_layout()
plt.savefig(ROOT / "results" / "pilot_curve.png", dpi=120)

print("\n=== PILOT AUDIT TABLE (step 10) ===")
for _, r in df.iterrows():
    print(f"\n[{r.financebench_id}] conf={r.confidence} grade={r.grade} ({r.grade_method})"
          f"{' SCALE-ERR' if r.scale_error else ''}")
    print(f"  Q: {r.question[:140]}")
    print(f"  gold: {str(r.gold)[:140]}")
    print(f"  ans:  {str(r.answer)[:140]}")
print(f"\nsnapshot: {df.model_snapshot.iloc[0]}")
print(f"pilot.csv + pilot_curve.png written. accuracy={(df.grade == 'correct').mean():.0%} refusals={df.refused.sum()}")
