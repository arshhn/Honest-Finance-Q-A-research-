"""Grading pass over the frozen raw_answers.csv (design.md v1.2 e/f/h).

Usage:
  python grade_all.py submit    - Python-grade numeric rows; submit grader +
                                  M2-agreement batches for everything text
  python grade_all.py finalize  - collect batches, freeze results/grades.csv
                                  and results/m2_agreement.csv
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from api_lib import download_batch, get_client, poll_batches
from grade_lib import gold_is_numeric, numeric_grade, extract_number
from prompts import AGREEMENT_PROMPT, GRADER_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "batch_raw"
IDS = ROOT / "results" / "grade_batch_ids.json"

df = pd.read_csv(ROOT / "results" / "raw_answers.csv")
df["answer"] = df.answer.fillna("")


def python_grades():
    """Grade what Python can; return (grades_df, rows needing AI grader)."""
    out, need_ai = [], []
    for _, r in df.iterrows():
        rec = {"custom_id": r.custom_id, "grade_method": None, "grade_primary": None,
               "scale_error": False, "grader_verdict": None}
        if r.expected == "refuse":
            rec.update(grade_method="compliance", grade_primary="refused" if r.refused else "answered")
        elif r.refused:
            rec.update(grade_method="refusal", grade_primary="refused")
        elif gold_is_numeric(str(r.gold_answer)):
            v, se = numeric_grade(str(r.gold_answer), str(r.answer), str(r.question_used))
            rec.update(grade_method="numeric_parser", grade_primary=v, scale_error=se)
            if v != "correct":
                need_ai.append(r)  # second opinion on parser-incorrect/unparsed
        else:
            rec.update(grade_method="ai_grader")
            need_ai.append(r)
        out.append(rec)
    return pd.DataFrame(out), need_ai


def m2_pairs():
    """FB oracle vs para answers per (qid, model). Returns numeric verdicts + judge requests."""
    fb = df[(df.dataset == "financebench") & df.setting.isin(["oracle", "para"])].copy()
    fb["qid"] = fb.instance_id.str.split("-").str[1]
    rows, judge_reqs = [], []
    for (qid, model), g in fb.groupby(["qid", "model"]):
        o = g[g.setting == "oracle"];  p = g[g.setting == "para"]
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
                judge_reqs.append({
                    "custom_id": f"m2-{qid}-{model}",
                    "params": {"model": "claude-sonnet-5", "max_tokens": 2000,
                               "messages": [{"role": "user", "content": AGREEMENT_PROMPT.format(
                                   question=str(o.question_used), a=str(o.answer), b=str(p.answer))}]},
                })
        rows.append(rec)
    return pd.DataFrame(rows), judge_reqs


def cmd_submit():
    grades, need_ai = python_grades()
    grades.to_csv(ROOT / "results" / "_grades_python_stage.csv", index=False)
    greqs = [{
        "custom_id": f"g--{r.custom_id}",
        "params": {"model": "claude-sonnet-5", "max_tokens": 2000,
                   "messages": [{"role": "user", "content": GRADER_PROMPT.format(
                       question=str(r.question_used), gold=str(r.gold_answer), candidate=str(r.answer))}]},
    } for r in need_ai]
    m2df, judge_reqs = m2_pairs()
    m2df.to_csv(ROOT / "results" / "_m2_python_stage.csv", index=False)

    client = get_client()
    ids = {}
    for name, reqs in [("grader", greqs), ("m2judge", judge_reqs)]:
        if not reqs:
            continue
        batch = client.messages.batches.create(requests=reqs)
        ids[name] = batch.id
        print(f"submitted {name}: {batch.id} ({len(reqs)} requests)")
    IDS.write_text(json.dumps(ids, indent=1))


def _verdict_map(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        out[r["custom_id"]] = r["text"].strip().upper()
    return out


def cmd_finalize():
    ids = json.loads(IDS.read_text())
    poll_batches(list(ids.values()))
    for name, bid in ids.items():
        out = RAW / f"{name}.results.jsonl"
        if not out.exists():
            download_batch(bid, out)

    grades = pd.read_csv(ROOT / "results" / "_grades_python_stage.csv")
    if "grader" in ids:
        v = _verdict_map(RAW / "grader.results.jsonl")
        word = {"CORRECT": "correct", "INCORRECT": "incorrect", "REFUSED": "refused"}
        gmap = {cid[3:]: word.get(t.split()[0] if t else "", "ungraded") for cid, t in v.items()}
        grades["grader_verdict"] = grades.custom_id.map(gmap)
        need = grades.grade_method == "ai_grader"
        grades.loc[need, "grade_primary"] = grades.loc[need, "grader_verdict"]
    out = ROOT / "results" / "grades.csv"
    if out.exists():
        raise SystemExit("grades.csv already frozen (hard rule 1)")
    grades.to_csv(out, index=False)
    print(f"FROZEN {out} ({len(grades)} rows)")
    print(grades.grade_primary.value_counts(dropna=False))

    m2 = pd.read_csv(ROOT / "results" / "_m2_python_stage.csv")
    if "m2judge" in ids:
        v = _verdict_map(RAW / "m2judge.results.jsonl")
        jmap = {cid: t.startswith("YES") for cid, t in v.items()}
        need = m2.method == "judge"
        m2.loc[need, "agree"] = m2[need].apply(lambda r: jmap.get(f"m2-{r.qid}-{r.model}"), axis=1)
    out2 = ROOT / "results" / "m2_agreement.csv"
    m2.to_csv(out2, index=False)
    print(f"FROZEN {out2} ({len(m2)} rows); agreement rate by model:")
    print(m2.groupby("model").agree.mean())


if __name__ == "__main__":
    {"submit": cmd_submit, "finalize": cmd_finalize}[sys.argv[1]]()
