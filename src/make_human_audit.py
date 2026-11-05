"""Reproduce the 30-grade human audit sample (design.md, Grading: "30 random grades hand-checked").

The sample is a simple random sample of all 1,708 rows of results/grades.csv,
drawn with random.Random(30303) over the sorted custom_ids. The original
drawing script was not preserved; this reconstruction (2026-11-06, rulebook
v1.8.4) reproduces the committed results/audit_sheet_human.csv IDs exactly.

Verify-only: it never writes or overwrites the audit sheet.
"""
import pathlib
import random

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = 30303
N = 30

grades = pd.read_csv(ROOT / "results" / "grades.csv")
sample = set(random.Random(SEED).sample(sorted(grades.custom_id), N))
sheet = set(pd.read_csv(ROOT / "results" / "audit_sheet_human.csv").custom_id)
print(f"seed {SEED}: {len(sample & sheet)}/{N} sampled IDs match results/audit_sheet_human.csv")
if sample != sheet:
    raise SystemExit("MISMATCH: the committed audit sheet is not the seed-30303 sample")
