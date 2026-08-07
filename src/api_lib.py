"""API helpers: client, sync threaded runs, batch submit/poll/download."""
import concurrent.futures as cf
import json
import pathlib
import time

import anthropic

ROOT = pathlib.Path(__file__).resolve().parents[1]


def get_client() -> anthropic.Anthropic:
    key = (ROOT / ".env").read_text().strip().split("=", 1)[1]
    return anthropic.Anthropic(api_key=key, max_retries=4)


def text_of(msg) -> str:
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def run_sync(requests: list[dict], workers: int = 6) -> dict[str, dict]:
    """requests: [{custom_id, params}] -> {custom_id: {model, text, stop_reason, usage}}"""
    client = get_client()
    out = {}

    def one(req):
        for attempt in range(3):
            try:
                msg = client.messages.create(**req["params"])
                return req["custom_id"], {
                    "model": msg.model, "text": text_of(msg),
                    "stop_reason": msg.stop_reason,
                    "in_tokens": msg.usage.input_tokens,
                    "out_tokens": msg.usage.output_tokens,
                }
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                if attempt == 2:
                    return req["custom_id"], {"model": "", "text": "", "stop_reason": f"ERROR:{e}",
                                              "in_tokens": 0, "out_tokens": 0}
                time.sleep(15 * (attempt + 1))

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for cid, res in ex.map(one, requests):
            out[cid] = res
    return out


def submit_batch(jsonl_path: pathlib.Path) -> str:
    client = get_client()
    reqs = [json.loads(line) for line in open(jsonl_path, encoding="utf-8")]
    batch = client.messages.batches.create(requests=reqs)
    print(f"submitted {jsonl_path.name}: {batch.id} ({len(reqs)} requests)")
    return batch.id


def poll_batches(batch_ids: list[str], interval: int = 120) -> None:
    client = get_client()
    pending = set(batch_ids)
    while pending:
        for bid in sorted(pending):
            b = client.messages.batches.retrieve(bid)
            c = b.request_counts
            print(f"  {bid}: {b.processing_status} ok={c.succeeded} err={c.errored} proc={c.processing}", flush=True)
            if b.processing_status == "ended":
                pending.discard(bid)
        if pending:
            time.sleep(interval)


def download_batch(batch_id: str, out_path: pathlib.Path) -> dict:
    """Write one JSON line per result: {custom_id, model, text, stop_reason, tokens, result_type}."""
    client = get_client()
    counts = {"succeeded": 0, "errored": 0, "other": 0}
    with open(out_path, "w", encoding="utf-8") as f:
        for result in client.messages.batches.results(batch_id):
            row = {"custom_id": result.custom_id, "result_type": result.result.type,
                   "model": "", "text": "", "stop_reason": "", "in_tokens": 0, "out_tokens": 0}
            if result.result.type == "succeeded":
                m = result.result.message
                row.update(model=m.model, text=text_of(m), stop_reason=m.stop_reason,
                           in_tokens=m.usage.input_tokens, out_tokens=m.usage.output_tokens)
                counts["succeeded"] += 1
            elif result.result.type == "errored":
                row["stop_reason"] = f"ERROR:{result.result.error}"
                counts["errored"] += 1
            else:
                counts["other"] += 1
            f.write(json.dumps(row) + "\n")
    print(f"downloaded {batch_id} -> {out_path.name} {counts}")
    return counts
