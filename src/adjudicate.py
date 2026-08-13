"""v1.7 adjudication: where the numeric parser was outvoted by BOTH the sonnet
grader and the opus auditor, the human-audit-analogous majority verdict stands.
grades.csv stays frozen; the analysis reads grades_final.csv.
"""
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
grades = pd.read_csv(ROOT / "results" / "grades.csv")
audit = pd.read_csv(ROOT / "results" / "audit_agreement.csv")

overrides = audit[(~audit.agree) & (audit.grade_method == "numeric_parser")]
g = grades.set_index("custom_id")
changed = []
for _, r in overrides.iterrows():
    grader = g.loc[r.custom_id, "grader_verdict"]
    if grader == r.audit_verdict:  # grader + auditor outvote parser
        g.loc[r.custom_id, "grade_primary"] = r.audit_verdict
        g.loc[r.custom_id, "grade_method"] = "adjudicated"
        changed.append(r.custom_id)
g.reset_index().to_csv(ROOT / "results" / "grades_final.csv", index=False)
print(f"adjudicated {len(changed)} rows -> grades_final.csv: {changed}")
