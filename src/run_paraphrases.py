"""Generate the 150 M2 paraphrases (sonnet-5, pinned prompt) -> data/paraphrases.csv."""
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from api_lib import run_sync
from prompts import PARAPHRASE_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[1]
fb = pd.read_csv(ROOT / "data" / "financebench.csv")

reqs = [{
    "custom_id": r.financebench_id,
    "params": {"model": "claude-sonnet-5", "max_tokens": 2000,
               "messages": [{"role": "user", "content": PARAPHRASE_PROMPT.format(question=r.question)}]},
} for _, r in fb.iterrows()]

print(f"generating {len(reqs)} paraphrases...")
res = run_sync(reqs, workers=6)
rows = [{"financebench_id": cid, "question": fb.set_index('financebench_id').loc[cid, 'question'],
         "paraphrase": r["text"].strip().strip('"')} for cid, r in res.items()]
out = pd.DataFrame(rows).sort_values("financebench_id")
bad = out[out.paraphrase.str.len() < 15]
assert bad.empty, f"suspiciously short paraphrases: {bad.financebench_id.tolist()}"
out.to_csv(ROOT / "data" / "paraphrases.csv", index=False)
print(f"frozen data/paraphrases.csv ({len(out)} rows)")
for _, r in out.head(5).iterrows():
    print(f"\nORIG: {r.question[:110]}\nPARA: {r.paraphrase[:110]}")
