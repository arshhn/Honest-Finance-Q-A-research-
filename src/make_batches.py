"""Pack the REMAINING FinanceBench sittings into multi-item exam papers.

Rationale (design.md changelog v1.5): one agent per question spends ~33k tokens of
harness overhead on a ~1k-token question. Packing many items into one sitting pays
that overhead once. Each item keeps the verbatim ask protocol and its own evidence;
an explicit independence instruction heads the paper.

Writes:
  data/prompts_batched/<batch_id>.txt
  data/batch_args.json            (workflow args: [{batch_id, path, model, n}])
  data/batch_manifest.csv         (batch_id -> instance ids, for auditing)
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harness_lib import journal_results

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "prompts_batched"
OUT.mkdir(parents=True, exist_ok=True)

MAX_ITEMS = 12
MAX_CHARS = 45_000
MODELS = ["haiku", "sonnet", "opus"]

HEADER = """You are sitting an exam made of {n} INDEPENDENT questions about company SEC filings.

Rules for the whole paper:
- Answer every item SEPARATELY. For each item use ONLY the document text inside that item.
- NEVER use information from one item to answer another, even if they concern the same company.
- Do not skip items. Follow each item's own instructions exactly.

"""

ITEM = """=== ITEM {k} | id={iid} ===
{prompt}

"""


def collected_ids() -> set:
    paths = json.loads((ROOT / "results" / "journals.json").read_text())
    got = set()
    for key in ("fb_main", "fb_para", "fsq"):
        for p in paths.get(key, []):
            try:
                got |= set(journal_results(p))
            except FileNotFoundError:
                pass
    return got


def main():
    equiv_n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    inst = pd.read_csv(ROOT / "data" / "instances_fb.csv").set_index("instance_id")
    got = collected_ids()

    wanted = [(iid, m) for iid in inst.index for m in MODELS]
    missing = [(iid, m) for iid, m in wanted if f"{iid}--{m}" not in got]
    print(f"instances={len(inst)} sittings wanted={len(wanted)} collected={len(wanted)-len(missing)} missing={len(missing)}")

    # equivalence check: re-ask a seeded sample of already-answered oracle items in batched form
    equiv = []
    if equiv_n:
        done_oracle = sorted(i for i in inst.index if i.endswith("-oracle")
                             and f"{i}--sonnet" in got)
        rng = __import__("random").Random(20260807)
        for iid in rng.sample(done_oracle, min(equiv_n, len(done_oracle))):
            equiv.append((iid, "sonnet"))
        print(f"equivalence re-asks: {len(equiv)} (sonnet, batched protocol)")

    prompts = {}
    for iid in inst.index:
        p = ROOT / "data" / "prompts" / f"{iid}.txt"
        if p.exists():
            prompts[iid] = p.read_text(encoding="utf-8")

    batches, manifest = [], []
    for model in MODELS:
        todo = [iid for iid, m in missing if m == model and iid in prompts]
        # longest first so packing is stable and big evidence never blocks a batch
        todo.sort(key=lambda i: (-len(prompts[i]), i))
        tag = "b"
        cur, cur_chars = [], 0
        def flush():
            nonlocal cur, cur_chars
            if not cur:
                return
            bid = f"{tag}{len(batches):04d}-{model}"
            body = HEADER.format(n=len(cur)) + "".join(
                ITEM.format(k=k + 1, iid=i, prompt=prompts[i]) for k, i in enumerate(cur))
            (OUT / f"{bid}.txt").write_text(body, encoding="utf-8")
            batches.append({"batch_id": bid, "path": str(OUT / f"{bid}.txt"),
                            "model": model, "n": len(cur),
                            "ids": [f"{i}--{model}" for i in cur]})
            manifest.extend({"batch_id": bid, "custom_id": f"{i}--{model}"} for i in cur)
            cur, cur_chars = [], 0
        for iid in todo:
            c = len(prompts[iid])
            if cur and (len(cur) >= MAX_ITEMS or cur_chars + c > MAX_CHARS):
                flush()
            cur.append(iid); cur_chars += c
        flush()

    # equivalence batches (marked so they never overwrite the primary rows)
    tag = "e"
    cur, cur_chars = [], 0
    for iid, model in equiv:
        c = len(prompts[iid])
        if cur and (len(cur) >= MAX_ITEMS or cur_chars + c > MAX_CHARS):
            bid = f"e{len(batches):04d}-sonnet"
            body = HEADER.format(n=len(cur)) + "".join(
                ITEM.format(k=k + 1, iid=i, prompt=prompts[i]) for k, i in enumerate(cur))
            (OUT / f"{bid}.txt").write_text(body, encoding="utf-8")
            batches.append({"batch_id": bid, "path": str(OUT / f"{bid}.txt"),
                            "model": "sonnet", "n": len(cur),
                            "ids": [f"{i}--sonnet" for i in cur], "equivalence": True})
            manifest.extend({"batch_id": bid, "custom_id": f"{i}--sonnet"} for i in cur)
            cur, cur_chars = [], 0
        cur.append(iid); cur_chars += c
    if cur:
        bid = f"e{len(batches):04d}-sonnet"
        body = HEADER.format(n=len(cur)) + "".join(
            ITEM.format(k=k + 1, iid=i, prompt=prompts[i]) for k, i in enumerate(cur))
        (OUT / f"{bid}.txt").write_text(body, encoding="utf-8")
        batches.append({"batch_id": bid, "path": str(OUT / f"{bid}.txt"),
                        "model": "sonnet", "n": len(cur),
                        "ids": [f"{i}--sonnet" for i in cur], "equivalence": True})
        manifest.extend({"batch_id": bid, "custom_id": f"{i}--sonnet"} for i in cur)

    (ROOT / "data" / "batch_args.json").write_text(json.dumps(batches))
    pd.DataFrame(manifest).to_csv(ROOT / "data" / "batch_manifest.csv", index=False)
    sittings = sum(b["n"] for b in batches)
    print(f"batches={len(batches)} sittings packed={sittings} "
          f"(avg {sittings/max(1,len(batches)):.1f}/batch)")
    print("est. overhead saving vs one-per-call: "
          f"{(1 - len(batches)/max(1,sittings))*100:.0f}%")


if __name__ == "__main__":
    main()
