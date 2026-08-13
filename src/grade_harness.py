"""Grading for the harness path (v1.3/v1.5): local Python grades + grader papers.

  python grade_harness.py stage     -> _grades_python_stage.csv, _m2_python_stage.csv,
                                       data/grading/g*.txt + j*.txt papers, grading_args.json
  python grade_harness.py finalize <journal> [<journal> ...]
                                    -> results/grades.csv, results/m2_agreement.csv
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grade_lib import gold_is_numeric, numeric_grade, extract_number
from harness_lib import journal_results
from prompts import AGREEMENT_PROMPT, GRADER_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[1]
GDIR = ROOT / "data" / "grading"
GDIR.mkdir(exist_ok=True)
MAX_PER_PAPER = 12

df = pd.read_csv(ROOT / "results" / "raw_answers.csv")
df["answer"] = df.answer.fillna("")


def python_grades():
    out, need_ai = [], []
    for _, r in df.iterrows():
        rec = {"custom_id": r.custom_id, "grade_method": None, "grade_primary": None,
               "scale_error": False, "grader_verdict": None}
        if r.expected == "refuse":
            rec.update(grade_method="compliance",
                       grade_primary="refused" if r.refused else "answered")
        elif r.refused:
            rec.update(grade_method="refusal", grade_primary="refused")
        elif gold_is_numeric(str(r.gold_answer)):
            v, se = numeric_grade(str(r.gold_answer), str(r.answer), str(r.question_used))
            rec.update(grade_method="numeric_parser", grade_primary=v, scale_error=se)
            if v != "correct":
                need_ai.append(r)          # second opinion on parser-negatives
        else:
            rec.update(grade_method="ai_grader")
            need_ai.append(r)
        out.append(rec)
    return pd.DataFrame(out), need_ai


def m2_pairs():
    fb = df[(df.dataset == "financebench") & df.setting.isin(["oracle", "para"])].copy()
    fb["qid"] = fb.instance_id.str.split("-").str[1]
    rows, judge = [], []
    for (qid, model), g in fb.groupby(["qid", "model"]):
        o = g[g.setting == "oracle"]; p = g[g.setting == "para"]
        if len(o) != 1 or len(p) != 1:
            continue
        o, p = o.iloc[0], p.iloc[0]
        rec = {"qid": qid, "model": model, "agree": None, "method": None}
        if o.refused or p.refused:
            rec.update(agree=False, method="refusal")
        else:
            no, np_ = extract_number(str(o.answer)), extract_number(str(p.answer))
            if no is not None and np_ is not None and gold_is_numeric(str(o.gold_answer)):
                same = (no == np_) or (no != 0 and abs(np_ - no) / abs(no) <= 0.01)
                rec.update(agree=bool(same), method="numeric")
            else:
                rec.update(method="judge")
                judge.append((qid, model, str(o.question_used), str(o.answer), str(p.answer)))
        rows.append(rec)
    return pd.DataFrame(rows), judge


def write_papers(blocks, prefix):
    papers = []
    for i in range(0, len(blocks), MAX_PER_PAPER):
        chunk = blocks[i:i + MAX_PER_PAPER]
        pid = f"{prefix}{len(papers):04d}"
        (GDIR / f"{pid}.txt").write_text("\n\n".join(b for _, b in chunk), encoding="utf-8")
        papers.append({"paper_id": pid, "path": str(GDIR / f"{pid}.txt"),
                       "n": len(chunk), "keys": [k for k, _ in chunk]})
    return papers


def cmd_stage():
    grades, need_ai = python_grades()
    grades.to_csv(ROOT / "results" / "_grades_python_stage.csv", index=False)
    gblocks = [(r.custom_id,
                f"=== ITEM id={r.custom_id} ===\n" + GRADER_PROMPT.format(
                    question=str(r.question_used), gold=str(r.gold_answer),
                    candidate=str(r.answer)))
               for r in need_ai]
    m2df, judge = m2_pairs()
    m2df.to_csv(ROOT / "results" / "_m2_python_stage.csv", index=False)
    jblocks = [(f"m2-{qid}-{model}",
                f"=== ITEM id=m2-{qid}-{model} ===\n" + AGREEMENT_PROMPT.format(
                    question=q, a=a, b=b))
               for qid, model, q, a, b in judge]
    papers = write_papers(gblocks, "g") + write_papers(jblocks, "j")
    (ROOT / "data" / "grading_args.json").write_text(json.dumps(
        [{"paper_id": p["paper_id"], "path": p["path"], "n": p["n"]} for p in papers],
        separators=(",", ":")))
    print(f"python-graded={len(grades)-len(need_ai)} ai-grade={len(gblocks)} "
          f"m2-judge={len(jblocks)} papers={len(papers)}")


def cmd_finalize(journals):
    res = {}
    for j in journals:
        res.update(journal_results(j))
    verdicts = {}
    for pid, r in res.items():
        for item in r.get("verdicts", []):
            verdicts[str(item.get("id", ""))] = str(item.get("verdict", "")).upper()
    print(f"verdicts returned: {len(verdicts)}")

    grades = pd.read_csv(ROOT / "results" / "_grades_python_stage.csv")
    word = {"CORRECT": "correct", "INCORRECT": "incorrect", "REFUSED": "refused"}
    grades["grader_verdict"] = grades.custom_id.map(
        lambda c: word.get(verdicts.get(c, ""), None))
    need = (grades.grade_method == "ai_grader")
    grades.loc[need, "grade_primary"] = grades.loc[need, "grader_verdict"]
    ungraded = int((need & grades.grade_primary.isna()).sum())
    out = ROOT / "results" / "grades.csv"
    if out.exists():
        raise SystemExit("grades.csv already frozen (hard rule 1)")
    grades.to_csv(out, index=False)
    dis = grades[(grades.grade_method == "numeric_parser")
                 & grades.grader_verdict.notna()
                 & (grades.grade_primary != grades.grader_verdict)]
    print(f"FROZEN grades.csv ({len(grades)}), ungraded={ungraded}, "
          f"parser-vs-grader disagreements={len(dis)}")
    print(grades.grade_primary.value_counts(dropna=False).to_string())

    m2 = pd.read_csv(ROOT / "results" / "_m2_python_stage.csv", dtype={"qid": str})
    jmap = {k[3:]: v.startswith("YES") for k, v in verdicts.items() if k.startswith("m2-")}
    need = m2.method == "judge"
    m2.loc[need, "agree"] = m2[need].apply(lambda r: jmap.get(f"{r.qid}-{r.model}"), axis=1)
    m2.to_csv(ROOT / "results" / "m2_agreement.csv", index=False)
    print(f"FROZEN m2_agreement.csv ({len(m2)}); agreement by model:")
    print(m2.assign(agree=m2.agree.astype(float)).groupby("model").agree.mean().round(3).to_string())


if __name__ == "__main__":
    if sys.argv[1] == "stage":
        cmd_stage()
    else:
        cmd_finalize(sys.argv[2:])
