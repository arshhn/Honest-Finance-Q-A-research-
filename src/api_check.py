"""One test call per tier: verify key, record exact model snapshots + rate-limit headers."""
import pathlib

import anthropic

ROOT = pathlib.Path(__file__).resolve().parents[1]
key = (ROOT / ".env").read_text().strip().split("=", 1)[1]
client = anthropic.Anthropic(api_key=key)

MODELS = ["claude-haiku-4-5", "claude-sonnet-5", "claude-opus-5"]

for m in MODELS:
    resp = client.messages.with_raw_response.create(
        model=m,
        max_tokens=64,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
    )
    msg = resp.parse()
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    h = resp.headers
    print(f"{m}: snapshot={msg.model} reply={text!r} stop={msg.stop_reason}")
    print(
        "  limits: req/min={} in-tok/min={} out-tok/min={}".format(
            h.get("anthropic-ratelimit-requests-limit"),
            h.get("anthropic-ratelimit-input-tokens-limit"),
            h.get("anthropic-ratelimit-output-tokens-limit"),
        )
    )
