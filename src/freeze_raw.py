"""Join batch results with instance metadata -> the frozen results/raw_answers.csv.

Hard rule 1: this file is written once, then analysis only ever reads it.
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grade_lib import parse_response

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "batch_raw"

inst = pd.concat([
    pd.read_csv(ROOT / "data" / "instances_fb.csv"),
    pd.read_csv(ROOT / "data" / "instances_fsq.csv"),
], ignore_index=True).set_index("instance_id")

rows = []
unknown = []
for f in sorted(RAW.glob("*.results.jsonl")):
    if f.name.endswith("_equiv.results.jsonl"):
        continue  # protocol-equivalence sample, frozen separately
    for line in open(f, encoding="utf-8"):
        r = json.loads(line)
        if "--" not in r["custom_id"]:
            unknown.append(r["custom_id"]); continue
        iid, model_short = r["custom_id"].split("--")
        if iid not in inst.index or model_short not in ("haiku", "sonnet", "opus"):
            unknown.append(r["custom_id"]); continue
        meta = inst.loc[iid]
        answer, conf, refused, parse_ok = parse_response(r["text"])
        rows.append({
            "custom_id": r["custom_id"], "instance_id": iid, "model": model_short,
            "model_snapshot": r["model"], "dataset": meta.dataset,
            "setting": meta.setting, "variant": meta.get("variant", ""),
            "expected": meta.expected, "question_used": meta.question_used,
            "gold_answer": meta.gold_answer, "raw_text": r["text"],
            "answer": answer, "confidence": conf, "refused": refused,
            "parse_ok": parse_ok, "stop_reason": r["stop_reason"],
            "result_type": r["result_type"],
            "in_tokens": r["in_tokens"], "out_tokens": r["out_tokens"],
            "protocol": r.get("protocol", "single"), "batch_id": r.get("batch_id", ""),
            "batch_file": f.name,
        })

df = pd.DataFrame(rows)
if unknown:
    print(f"WARNING: {len(unknown)} rows with unrecognised ids dropped, e.g. {unknown[:5]}")
dupes = df.custom_id.duplicated().sum()
if dupes:
    print(f"WARNING: {dupes} duplicate custom_ids; keeping first (single protocol wins)")
    df = df.sort_values("protocol").drop_duplicates("custom_id", keep="first")
wanted = {f"{i}--{m}" for i in inst.index for m in ("haiku", "sonnet", "opus")}
missing = wanted - set(df.custom_id)
print(f"coverage: {len(df)}/{len(wanted)} sittings; missing {len(missing)}")
if missing:
    print("  e.g.", sorted(missing)[:8])
out = ROOT / "results" / "raw_answers.csv"
if out.exists():
    raise SystemExit("raw_answers.csv already exists - frozen files are sacred (hard rule 1). "
                     "Delete manually only with a changelog entry.")
df.to_csv(out, index=False)
print(f"FROZEN {out} ({len(df)} rows)")
print(df.groupby(["dataset", "model"]).size())
print("errored:", (df.result_type != "succeeded").sum(),
      "| truncated:", (df.stop_reason == "max_tokens").sum(),
      "| unparsed:", (~df.parse_ok & ~df.refused).sum())
