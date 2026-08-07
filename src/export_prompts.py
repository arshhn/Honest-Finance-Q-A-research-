"""Explode batch request JSONLs into one prompt file per instance for harness agents.

data/prompts/<instance_id>.txt  (same prompt is reused across the 3 models)
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "prompts"
OUT.mkdir(parents=True, exist_ok=True)

sources = ["fb_all.jsonl", "fb_para.jsonl", "fsq_haiku.jsonl"]  # fsq: any one model file has every instance prompt
n = 0
for name in sources:
    p = ROOT / "results" / "batch_requests" / name
    if not p.exists():
        print(f"skip {name} (not built yet)")
        continue
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        iid = r["custom_id"].split("--")[0]
        f = OUT / f"{iid}.txt"
        if not f.exists():
            f.write_text(r["params"]["messages"][0]["content"], encoding="utf-8")
            n += 1
print(f"wrote {n} new prompt files -> {OUT}")
