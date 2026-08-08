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


def batched_results(journal_path) -> dict:
    """custom_id -> row, from a multi-item exam-paper journal (design.md v1.5).

    Each agent returns {batch_id, results:[{id, answer, confidence}]}; `id` is the
    instance id, so the custom_id is id--<model of that batch>.
    """
    out = {}
    for line in open(journal_path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("type") != "result" or not isinstance(r.get("result"), dict):
            continue
        res = r["result"]
        bid = res.get("batch_id", "")
        if not bid or "results" not in res:
            continue
        model_short = bid.rsplit("-", 1)[-1]
        equivalence = bid.startswith("e")
        for item in res["results"]:
            iid = str(item.get("id", "")).strip()
            if not iid:
                continue
            cid = f"{iid}--{model_short}"
            out[cid] = {
                "custom_id": cid, "answer": item.get("answer", ""),
                "confidence": item.get("confidence"),
                "batch_id": bid, "equivalence": equivalence,
            }
    return out


def batched_to_batchraw(journal_paths, out_path, protocol="batched"):
    """Write batch_raw-schema rows from one or more exam-paper journals.

    Equivalence-check rows (batch ids starting with 'e') are written to a sibling
    file so they never overwrite the primary single-protocol rows.
    """
    primary, equiv = {}, {}
    for p in journal_paths:
        for cid, row in batched_results(p).items():
            (equiv if row["equivalence"] else primary)[cid] = row

    def dump(rows, path):
        with open(path, "w", encoding="utf-8") as f:
            for cid, r in sorted(rows.items()):
                model_short = cid.split("--")[1]
                conf = r["confidence"]
                text = f"ANSWER: {r['answer']}\nCONFIDENCE: {conf if conf is not None else ''}"
                f.write(json.dumps({
                    "custom_id": cid, "result_type": "succeeded",
                    "model": SNAPSHOTS[model_short], "text": text,
                    "stop_reason": "end_turn", "in_tokens": 0, "out_tokens": 0,
                    "protocol": protocol, "batch_id": r["batch_id"],
                }) + "\n")
        return len(rows)

    n1 = dump(primary, out_path)
    p2 = pathlib.Path(str(out_path).replace(".results.jsonl", "_equiv.results.jsonl"))
    n2 = dump(equiv, p2) if equiv else 0
    return n1, n2


if __name__ == "__main__":
    import sys
    n = to_batchraw(sys.argv[1], sys.argv[2])
    print(f"converted {n} results -> {sys.argv[2]}")
