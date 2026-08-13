"""Convert all subject journals -> results/batch_raw/*.results.jsonl.

Single-protocol journals (one agent per question, v1.3) and batched exam-paper
journals (v1.5) both land in the same schema, tagged with `protocol`.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harness_lib import SNAPSHOTS, batched_to_batchraw, journal_results

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "batch_raw"
RAW.mkdir(parents=True, exist_ok=True)

paths = json.loads((ROOT / "results" / "journals.json").read_text())


def dump_single(keys, out_name):
    rows = {}
    for key in keys:
        for p in paths.get(key, []):
            if pathlib.Path(p).exists():
                rows.update(journal_results(p))
    out = RAW / out_name
    with open(out, "w", encoding="utf-8") as f:
        for cid, r in sorted(rows.items()):
            model_short = cid.split("--")[1]
            text = r.get("full_text") or (
                f"ANSWER: {r.get('answer','')}\nCONFIDENCE: {r.get('confidence','')}")
            f.write(json.dumps({
                "custom_id": cid, "result_type": "succeeded",
                "model": SNAPSHOTS[model_short], "text": text,
                "stop_reason": "end_turn", "in_tokens": 0, "out_tokens": 0,
                "protocol": "single", "batch_id": "",
            }) + "\n")
    return len(rows)


n_single = dump_single(["fb_main", "fb_para"], "fb_single.results.jsonl")
bj = [p for p in paths.get("fb_batched", []) if pathlib.Path(p).exists()]
n_batched, n_equiv = batched_to_batchraw(bj, RAW / "fb_batched.results.jsonl") if bj else (0, 0)
fj = [p for p in paths.get("fsq", []) if pathlib.Path(p).exists()]
n_fsq, _ = batched_to_batchraw(fj, RAW / "fsq_batched.results.jsonl") if fj else (0, 0)
print(f"single={n_single} batched={n_batched} equivalence={n_equiv} fsq={n_fsq}")
