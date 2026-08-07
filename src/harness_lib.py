"""Harness-mode helpers: convert workflow journal.jsonl -> batch_raw-schema JSONL
so freeze_raw.py and everything downstream works unchanged (design.md v1.3)."""
import json
import pathlib

SNAPSHOTS = {
    "haiku": "harness:claude-haiku-4-5-20251001",
    "sonnet": "harness:claude-sonnet-5",
    "opus": "harness:claude-opus-5",
}


def journal_results(journal_path) -> dict:
    """custom_id -> structured result (last write wins across resumes)."""
    out = {}
    for line in open(journal_path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("type") == "result" and isinstance(r.get("result"), dict):
            res = r["result"]
            if "custom_id" in res:
                out[res["custom_id"]] = res
    return out


def to_batchraw(journal_path, out_path, append=False):
    """Write batch_raw-schema rows from a subjects journal."""
    res = journal_results(journal_path)
    mode = "a" if append else "w"
    with open(out_path, mode, encoding="utf-8") as f:
        for cid, r in sorted(res.items()):
            model_short = cid.split("--")[1]
            text = r.get("full_text") or f"ANSWER: {r.get('answer','')}\nCONFIDENCE: {r.get('confidence','')}"
            f.write(json.dumps({
                "custom_id": cid, "result_type": "succeeded",
                "model": SNAPSHOTS[model_short], "text": text,
                "stop_reason": "end_turn", "in_tokens": 0, "out_tokens": 0,
            }) + "\n")
    return len(res)


if __name__ == "__main__":
    import sys
    n = to_batchraw(sys.argv[1], sys.argv[2])
    print(f"converted {n} results -> {sys.argv[2]}")
