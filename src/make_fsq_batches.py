"""Pack the FailSafeQA subset (design.md changelog v1.6 scope cut) into exam papers.

FailSafeQA items carry whole filings (~32k tokens each), so unlike FinanceBench the
cost is irreducible content, not harness overhead. Under Hard Rule 6 we run a seeded
subset of items rather than slipping the sprint or touching the FinanceBench core.

Writes data/prompts_batched/f*.txt and data/fsq_batch_args.json
"""
import json
import pathlib
import random
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harness_lib import journal_results

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "prompts_batched"
OUT.mkdir(parents=True, exist_ok=True)

N_ITEMS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
SEED = 20260807
MODELS = ["haiku", "sonnet", "opus"]
MAX_ITEMS = 3
MAX_CHARS = 380_000  # ~105k tokens of content; fits every tier's context with headroom

HEADER = """You are sitting an exam made of {n} INDEPENDENT questions about company SEC filings.

Rules for the whole paper:
- Answer every item SEPARATELY. For each item use ONLY the document text inside that item.
- NEVER use information from one item to answer another.
- Do not skip items. Follow each item's own instructions exactly.

"""
ITEM = """=== ITEM {k} | id={iid} ===
{prompt}

"""


def main():
    inst = pd.read_csv(ROOT / "data" / "instances_fsq.csv")
    idxs = sorted(inst.idx.unique())
    chosen = sorted(int(i) for i in random.Random(SEED).sample(list(idxs), min(N_ITEMS, len(idxs))))
    sub = inst[inst.idx.isin(chosen)]
    (ROOT / "data" / "fsq_subset_ids.json").write_text(json.dumps(chosen))
    print(f"seeded subset: {len(chosen)}/{len(idxs)} items -> {len(sub)} instances/model")
    print("  conditions:", sub.setting.value_counts().to_dict())
    print("  pert variants:", sub[sub.setting == 'pert'].variant.value_counts().to_dict())
    print("  unans variants:", sub[sub.setting == 'unans'].variant.value_counts().to_dict())

    got = set()
    paths = json.loads((ROOT / "results" / "journals.json").read_text())
    for p in paths.get("fsq", []):
        if pathlib.Path(p).exists():
            got |= set(journal_results(p))

    prompts = {}
    for iid in sub.instance_id:
        p = ROOT / "data" / "prompts" / f"{iid}.txt"
        if p.exists():
            prompts[iid] = p.read_text(encoding="utf-8")
    print(f"prompt files found: {len(prompts)}/{len(sub)}")

    batches, manifest = [], []
    for model in MODELS:
        todo = [i for i in sub.instance_id if i in prompts and f"{i}--{model}" not in got]
        todo.sort(key=lambda i: (-len(prompts[i]), i))
        cur, cur_chars = [], 0

        def flush():
            nonlocal cur, cur_chars
            if not cur:
                return
            bid = f"f{len(batches):04d}-{model}"
            body = HEADER.format(n=len(cur)) + "".join(
                ITEM.format(k=k + 1, iid=i, prompt=prompts[i]) for k, i in enumerate(cur))
            (OUT / f"{bid}.txt").write_text(body, encoding="utf-8")
            batches.append({"batch_id": bid, "path": str(OUT / f"{bid}.txt"),
                            "model": model, "n": len(cur)})
            manifest.extend({"batch_id": bid, "custom_id": f"{i}--{model}"} for i in cur)
            cur, cur_chars = [], 0

        for iid in todo:
            c = len(prompts[iid])
            if cur and (len(cur) >= MAX_ITEMS or cur_chars + c > MAX_CHARS):
                flush()
            cur.append(iid); cur_chars += c
        flush()

    (ROOT / "data" / "fsq_batch_args.json").write_text(
        json.dumps(batches, separators=(",", ":")))
    pd.DataFrame(manifest).to_csv(ROOT / "data" / "fsq_batch_manifest.csv", index=False)
    sittings = sum(b["n"] for b in batches)
    chars = sum(len((OUT / f"{b['batch_id']}.txt").read_text(encoding='utf-8')) for b in batches)
    print(f"batches={len(batches)} sittings={sittings} content~{chars/3.6/1e6:.1f}M tokens")


if __name__ == "__main__":
    main()
