"""Build the opus cross-audit papers (design v1.2h): 60 seeded grades + all
parser/grader disagreements + rows from the classifier-gap paper (f0020-haiku).
"""
import json
import pathlib
import random
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import GRADER_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[1]
GDIR = ROOT / "data" / "grading"

raw = pd.read_csv(ROOT / "results" / "raw_answers.csv")
grades = pd.read_csv(ROOT / "results" / "grades.csv")
m = raw.merge(grades, on="custom_id")

gradeable = m[m.grade_primary.isin(["correct", "incorrect"])]
rng = random.Random(20260807)
sample_ids = set(rng.sample(sorted(gradeable.custom_id), 60))
dis = set(grades[(grades.grade_method == "numeric_parser")
                 & grades.grader_verdict.notna()
                 & (grades.grade_primary != grades.grader_verdict)].custom_id)
f0020 = set(m[(m.batch_id == "f0020-haiku") & m.grade_primary.isin(["correct", "incorrect"])].custom_id)
chosen = sorted(sample_ids | dis | f0020)
sub = m[m.custom_id.isin(chosen)]
print(f"audit rows: {len(sub)} (sample 60, disagreements {len(dis)}, f0020 {len(f0020)})")

papers = []
blocks = [(r.custom_id, f"=== ITEM id={r.custom_id} ===\n" + GRADER_PROMPT.format(
    question=str(r.question_used), gold=str(r.gold_answer), candidate=str(r.answer)))
    for _, r in sub.iterrows()]
for i in range(0, len(blocks), 10):
    chunk = blocks[i:i + 10]
    pid = f"a{len(papers):04d}"
    (GDIR / f"{pid}.txt").write_text("\n\n".join(b for _, b in chunk), encoding="utf-8")
    papers.append({"paper_id": pid, "path": str(GDIR / f"{pid}.txt"), "n": len(chunk)})
(ROOT / "data" / "audit_args.json").write_text(json.dumps(papers, separators=(",", ":")))
sub[["custom_id", "grade_primary", "grade_method"]].to_csv(
    ROOT / "results" / "_audit_targets.csv", index=False)
print(f"audit papers: {len(papers)}")
