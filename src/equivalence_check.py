"""v1.5 pre-registered equivalence check: single vs batched protocol on 30 seeded
already-answered sonnet oracle questions. Writes results/equivalence_check.csv.
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grade_lib import gold_is_numeric, numeric_grade, parse_response, extract_number

ROOT = pathlib.Path(__file__).resolve().parents[1]

raw = pd.read_csv(ROOT / "results" / "raw_answers.csv").set_index("custom_id")
rows = []
for line in open(ROOT / "results" / "batch_raw" / "fb_batched_equiv.results.jsonl", encoding="utf-8"):
    r = json.loads(line)
    cid = r["custom_id"]
    if cid not in raw.index:
        continue
    orig = raw.loc[cid]
    b_ans, b_conf, b_ref, _ = parse_response(r["text"])
    rec = {"custom_id": cid,
           "single_refused": bool(orig.refused), "batched_refused": bool(b_ref),
           "single_conf": orig.confidence, "batched_conf": b_conf,
           "gold_numeric": gold_is_numeric(str(orig.gold_answer))}
    if rec["gold_numeric"]:
        rec["single_correct"] = numeric_grade(str(orig.gold_answer), str(orig.answer),
                                              str(orig.question_used))[0] == "correct"
        rec["batched_correct"] = numeric_grade(str(orig.gold_answer), str(b_ans),
                                               str(orig.question_used))[0] == "correct"
        a, b = extract_number(str(orig.answer)), extract_number(str(b_ans))
        rec["answers_match"] = (a is not None and b is not None
                                and (a == b or (a != 0 and abs(b - a) / abs(a) <= 0.01)))
    rows.append(rec)

df = pd.DataFrame(rows)
df.to_csv(ROOT / "results" / "equivalence_check.csv", index=False)
n = len(df)
num = df[df.gold_numeric]
print(f"pairs compared: {n} (numeric-gold: {len(num)})")
print(f"refusal rate   single={df.single_refused.mean():.3f}  batched={df.batched_refused.mean():.3f}")
print(f"mean confidence single={df.single_conf.mean():.1f}  batched={df.batched_conf.mean():.1f}")
if len(num):
    print(f"numeric accuracy single={num.single_correct.mean():.3f}  batched={num.batched_correct.mean():.3f}")
    print(f"numeric answers match across protocols: {num.answers_match.mean():.3f}")
