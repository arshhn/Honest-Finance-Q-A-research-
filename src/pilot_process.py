"""Process the harness pilot: journal -> parse -> python grading -> audit table.

Usage:
  python pilot_process.py stage <journal_path>   # writes pilot rows + grading file for text answers
  python pilot_process.py finalize <grader_journal_path|none>  # merge verdicts -> results/pilot.csv + curve
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grade_lib import gold_is_numeric, numeric_grade, parse_response
from harness_lib import journal_results
from prompts import GRADER_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "results" / "_pilot_stage.csv"


def stage(journal_path):
    fb = pd.read_csv(ROOT / "data" / "financebench.csv").set_index("financebench_id")
    res = journal_results(journal_path)
    rows = []
    for cid, r in sorted(res.items()):
        fid = "financebench_id_" + cid.split("-")[1]
        meta = fb.loc[fid]
        text = r.get("full_text", "")
        answer, conf, refused, parse_ok = parse_response(text)
        rows.append({"custom_id": cid, "financebench_id": fid,
                     "model_snapshot": "harness:claude-sonnet-5",
                     "question": meta.question, "gold": meta.answer,
                     "raw_text": text, "answer": answer, "confidence": conf,
                     "refused": refused, "parse_ok": parse_ok})
    df = pd.DataFrame(rows)
    grades, scale_errs, methods = [], [], []
    pending = []
    for i, row in df.iterrows():
        if row.refused:
            grades.append("refused"); scale_errs.append(False); methods.append("refusal")
        elif gold_is_numeric(str(row.gold)):
            v, se = numeric_grade(str(row.gold), str(row.answer), str(row.question))
            grades.append(v); scale_errs.append(se); methods.append("numeric_parser")
        else:
            grades.append(None); scale_errs.append(False); methods.append("ai_grader")
            pending.append(i)
    df["grade"], df["scale_error"], df["grade_method"] = grades, scale_errs, methods
    df.to_csv(STAGE, index=False)
    # grading file for one batched grader agent
    gpath = ROOT / "data" / "grading" / "pilot_grading.txt"
    gpath.parent.mkdir(exist_ok=True)
    blocks = []
    for i in pending:
        r = df.loc[i]
        blocks.append(f"=== ITEM {i} ===\n" + GRADER_PROMPT.format(
            question=r.question, gold=r.gold, candidate=r.answer))
    gpath.write_text("\n\n".join(blocks) if blocks else "NO ITEMS", encoding="utf-8")
    print(f"staged {len(df)} rows; {len(pending)} need AI grading -> {gpath}")
    print("pending item indices:", pending)


def finalize(grader_journal):
    df = pd.read_csv(STAGE)
    if grader_journal != "none":
        res = journal_results(grader_journal)
        verdicts = res.get("pilot-grader", {}).get("verdicts", [])
        for v in verdicts:
            df.loc[int(v["item"]), "grade"] = v["verdict"].lower()
    out = ROOT / "results" / "pilot.csv"
    df.to_csv(out, index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = df[~df.refused & df.confidence.notna()].sort_values("confidence", ascending=False)
    xs, ys = [], []
    for t in sorted(d.confidence.unique(), reverse=True):
        sel = d[d.confidence >= t]
        xs.append(len(sel) / len(df)); ys.append((sel.grade != "correct").mean())
    plt.figure(figsize=(5, 4))
    plt.plot(xs, ys, "o-")
    plt.xlabel("coverage"); plt.ylabel("risk among answered")
    plt.title("Pilot mini risk-coverage (10 Q, sonnet, M1)")
    plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(ROOT / "results" / "pilot_curve.png", dpi=120)

    print("=== PILOT AUDIT TABLE ===")
    for _, r in df.iterrows():
        print(f"\n[{r.financebench_id}] conf={r.confidence} grade={r.grade} ({r.grade_method})"
              f"{' SCALE-ERR' if r.scale_error else ''} refused={r.refused}")
        print(f"  Q:    {str(r.question)[:150]}")
        print(f"  gold: {str(r.gold)[:150]}")
        print(f"  ans:  {str(r.answer)[:150]}")
    print(f"\nfrozen results/pilot.csv | accuracy={(df.grade=='correct').mean():.0%} refusals={int(df.refused.sum())}")


if __name__ == "__main__":
    if sys.argv[1] == "stage":
        stage(sys.argv[2])
    else:
        finalize(sys.argv[2])
