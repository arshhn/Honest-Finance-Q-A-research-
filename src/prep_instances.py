"""Build all experiment instances + Message Batches request files.

Deterministic: everything derives from the frozen CSVs/JSON in data/ plus the
pinned rules in design.md changelog v1.2. Rerunning overwrites identically.

Outputs:
  data/instances_fb.csv    - FinanceBench instances (oracle + closedbook [+ para later])
  data/instances_fsq.csv   - FailSafeQA instances (base / pert / unans per item)
  data/pilot_ids.txt       - 10 seeded FinanceBench ids for the pilot
  results/batch_requests/fb_all.jsonl        (oracle+closedbook, all 3 models)
  results/batch_requests/fsq_{model}.jsonl   (one per model)
Run again with --with-para once data/paraphrases.csv exists to emit
  results/batch_requests/fb_para.jsonl
"""
import ast
import json
import pathlib
import random
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import CLOSEDBOOK_TEMPLATE, MISSING_DOC_TEXT, ORACLE_TEMPLATE

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQ_DIR = ROOT / "results" / "batch_requests"
REQ_DIR.mkdir(parents=True, exist_ok=True)

MODELS = {"haiku": "claude-haiku-4-5", "sonnet": "claude-sonnet-5", "opus": "claude-opus-5"}
MAX_TOKENS = 8000
SEP = "\n\n---\n\n"


def fb_qid(financebench_id: str) -> str:
    return financebench_id.replace("financebench_id_", "")


def oracle_evidence(evidence_field: str) -> str:
    items = ast.literal_eval(evidence_field)
    pages, seen = [], set()
    for it in items:
        page = it.get("evidence_text_full_page") or it["evidence_text"]
        if page not in seen:
            seen.add(page)
            pages.append(page)
    return SEP.join(pages)


def request(custom_id: str, model_id: str, prompt: str) -> dict:
    return {
        "custom_id": custom_id,
        "params": {
            "model": model_id,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        },
    }


def build_fb(with_para: bool):
    fb = pd.read_csv(ROOT / "data" / "financebench.csv")
    para = None
    if with_para:
        para = pd.read_csv(ROOT / "data" / "paraphrases.csv").set_index("financebench_id")["paraphrase"]

    inst_rows, reqs_main, reqs_para = [], [], []
    for _, r in fb.iterrows():
        qid = fb_qid(r.financebench_id)
        ev = oracle_evidence(r.evidence)
        settings = {
            "oracle": ORACLE_TEMPLATE.format(evidence=ev, question=r.question),
            "closedbook": CLOSEDBOOK_TEMPLATE.format(question=r.question),
        }
        if with_para:
            settings["para"] = ORACLE_TEMPLATE.format(evidence=ev, question=para[r.financebench_id])
        for setting, prompt in settings.items():
            iid = f"fb-{qid}-{setting}"
            inst_rows.append({
                "instance_id": iid, "dataset": "financebench",
                "financebench_id": r.financebench_id, "setting": setting,
                "question_used": para[r.financebench_id] if setting == "para" else r.question,
                "gold_answer": r.answer, "expected": "answer",
                "evidence_chars": 0 if setting == "closedbook" else len(ev),
                "prompt_chars": len(prompt),
            })
            bucket = reqs_para if setting == "para" else reqs_main
            for short, model_id in MODELS.items():
                bucket.append(request(f"{iid}--{short}", model_id, prompt))

    inst = pd.DataFrame(inst_rows)
    if with_para:  # keep previously-written oracle/closedbook rows consistent: rewrite all
        pass
    inst.to_csv(ROOT / "data" / "instances_fb.csv", index=False)
    with open(REQ_DIR / "fb_all.jsonl", "w", encoding="utf-8") as f:
        for q in reqs_main:
            f.write(json.dumps(q) + "\n")
    if with_para:
        with open(REQ_DIR / "fb_para.jsonl", "w", encoding="utf-8") as f:
            for q in reqs_para:
                f.write(json.dumps(q) + "\n")
    return inst, len(reqs_main), len(reqs_para)


PERT_NAMES = ["misspelled", "incomplete", "outofdomain", "ocr"]
UNANS_NAMES = ["missingctx", "outofscope"]


def build_fsq():
    data = json.load(open(ROOT / "data" / "failsafeqa_raw.jsonl", encoding="utf-8"))
    inst_rows = []
    reqs = {short: [] for short in MODELS}
    for item in data:
        idx = int(item["idx"])
        pert = PERT_NAMES[idx % 4]
        unans = UNANS_NAMES[idx % 2]
        conds = {
            "base": (item["query"], item["context"], "answer", "base"),
            "pert": {
                "misspelled": (item["error_query"], item["context"], "answer", pert),
                "incomplete": (item["incomplete_query"], item["context"], "answer", pert),
                "outofdomain": (item["out-of-domain_query"], item["context"], "answer", pert),
                "ocr": (item["query"], item["ocr_context"], "answer", pert),
            }[pert],
            "unans": {
                "missingctx": (item["query"], MISSING_DOC_TEXT, "refuse", unans),
                "outofscope": (item["out-of-scope_query"], item["context"], "refuse", unans),
            }[unans],
        }
        for cond, (query, ctx, expected, variant) in conds.items():
            iid = f"fsq-{idx:03d}-{cond}"
            prompt = ORACLE_TEMPLATE.format(evidence=ctx, question=query)
            inst_rows.append({
                "instance_id": iid, "dataset": "failsafeqa", "idx": idx,
                "setting": cond, "variant": variant, "question_used": query,
                "gold_answer": item["answer"], "expected": expected,
                "evidence_chars": len(ctx), "prompt_chars": len(prompt),
            })
            for short, model_id in MODELS.items():
                reqs[short].append(request(f"{iid}--{short}", model_id, prompt))

    pd.DataFrame(inst_rows).to_csv(ROOT / "data" / "instances_fsq.csv", index=False)
    sizes = {}
    for short, rows in reqs.items():
        p = REQ_DIR / f"fsq_{short}.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for q in rows:
                f.write(json.dumps(q) + "\n")
        sizes[short] = (len(rows), p.stat().st_size / 1e6)
    return pd.DataFrame(inst_rows), sizes


def pilot_ids():
    fb = pd.read_csv(ROOT / "data" / "financebench.csv")
    rng = random.Random(42)
    ids = sorted(rng.sample(sorted(fb.financebench_id), 10))
    (ROOT / "data" / "pilot_ids.txt").write_text("\n".join(ids) + "\n")
    return ids


if __name__ == "__main__":
    with_para = "--with-para" in sys.argv
    inst_fb, n_main, n_para = build_fb(with_para)
    inst_fsq, sizes = build_fsq()
    ids = pilot_ids()
    print(f"FB instances: {len(inst_fb)} | batch reqs main={n_main} para={n_para}")
    print(f"FSQ instances: {len(inst_fsq)}")
    for short, (n, mb) in sizes.items():
        print(f"  fsq_{short}.jsonl: {n} requests, {mb:.1f} MB")
    print("FSQ variant counts:", inst_fsq[inst_fsq.setting == 'pert'].variant.value_counts().to_dict(),
          inst_fsq[inst_fsq.setting == 'unans'].variant.value_counts().to_dict())
    # cost estimate: chars/3.6 ~ tokens (finance text with tables ~3.5-3.8 chars/token)
    tok_fb = inst_fb.prompt_chars.sum() / 3.6 * 3  # x3 models
    tok_fsq = inst_fsq.prompt_chars.sum() / 3.6 * 3
    print(f"pilot ids: {ids}")
    print(f"approx input tokens: FB {tok_fb/1e6:.1f}M x3models | FSQ {tok_fsq/1e6:.1f}M (already x3? no: x3 applied)")
    # batch pricing per M input: haiku .5, sonnet 1.0(intro), opus 2.5 -> avg 1.33
    est = (tok_fb / 3 + tok_fsq / 3) / 1e6 * (0.5 + 1.0 + 2.5)
    print(f"rough input cost estimate (batch pricing, all 3 models): ${est:.0f}")
