"""Submit main experiment batches. Usage:
  python run_batches.py submit fb_all fb_para fsq_haiku fsq_sonnet fsq_opus
  python run_batches.py poll
  python run_batches.py collect
Batch ids persist in results/batch_ids.json (append-safe).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from api_lib import download_batch, poll_batches, submit_batch

ROOT = pathlib.Path(__file__).resolve().parents[1]
IDS = ROOT / "results" / "batch_ids.json"
RAW = ROOT / "results" / "batch_raw"
RAW.mkdir(parents=True, exist_ok=True)


def load_ids() -> dict:
    return json.loads(IDS.read_text()) if IDS.exists() else {}


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    ids = load_ids()
    if cmd == "submit":
        for name in args:
            if name in ids:
                print(f"{name} already submitted: {ids[name]}"); continue
            ids[name] = submit_batch(ROOT / "results" / "batch_requests" / f"{name}.jsonl")
            IDS.write_text(json.dumps(ids, indent=1))
    elif cmd == "poll":
        poll_batches(list(ids.values()))
    elif cmd == "collect":
        for name, bid in ids.items():
            out = RAW / f"{name}.results.jsonl"
            if out.exists():
                print(f"{name}: already collected"); continue
            download_batch(bid, out)
    else:
        raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
