"""Generate notebooks/01_runs.ipynb (pipeline documentation) and
notebooks/02_analysis.ipynb (Run-All analysis from frozen CSVs, Colab-compatible).
"""
import pathlib

import nbformat as nbf

ROOT = pathlib.Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)
REPO = "https://github.com/arshhn/honest-finance-qa"


def md(s):
    return nbf.v4.new_markdown_cell(s)


def code(s):
    return nbf.v4.new_code_cell(s)


# ---------------- 01_runs ----------------
nb1 = nbf.v4.new_notebook()
nb1.cells = [
    md(f"""# 01 — How the experiment was run

This notebook **documents** the run pipeline (it needs an `ANTHROPIC_API_KEY` with
credits to actually execute, so treat it as a recipe; the outputs it produced are
frozen in `results/` and analyzed — without any API key — in `02_analysis.ipynb`).

**Design**: see `docs/design.md` (rulebook v1.2, every decision pre-registered in its changelog).

The pipeline, in order:

| step | command | output (frozen) |
|---|---|---|
| 1. build instances + batch request files | `python src/prep_instances.py` | `data/instances_*.csv` |
| 2. pilot (10 Q × Sonnet, audited) | `python src/run_pilot.py` | `results/pilot.csv` |
| 3. M2 paraphrases | `python src/run_paraphrases.py` | `data/paraphrases.csv` |
| 4. rebuild with paraphrase requests | `python src/prep_instances.py --with-para` | — |
| 5. submit batches (Message Batches API) | `python src/run_batches.py submit fb_all fb_para fsq_haiku fsq_sonnet fsq_opus` | `results/batch_ids.json` |
| 6. wait + download | `python src/run_batches.py poll` / `collect` | `results/batch_raw/` |
| 7. freeze raw outputs (sacred) | `python src/freeze_raw.py` | `results/raw_answers.csv` |
| 8. grade (Python numeric + pinned AI grader) | `python src/grade_all.py submit` / `finalize` | `results/grades.csv`, `results/m2_agreement.csv` |

Repo: {REPO}
"""),
    md("""## The ask protocol (verbatim)

Every model sees exactly this (from `src/prompts.py`, pinned):

```
You are answering a question about a company's SEC filing. Use ONLY the provided document text.
Document: {evidence}
Question: {question}
Rules: If the document does not contain enough information, reply exactly "CANNOT ANSWER".
Reply in this format —
ANSWER: <your answer, with units>
CONFIDENCE: <integer 0–100, how likely your answer is correct>
```

Models (exact snapshots recorded per row in `raw_answers.csv`):
small = `claude-haiku-4-5`, mid = `claude-sonnet-5`, large = `claude-opus-5`,
each at its API defaults (no temperature/thinking/effort overrides — see changelog v1.2b).
"""),
]
nbf.write(nb1, NB / "01_runs.ipynb")

# ---------------- 02_analysis ----------------
nb2 = nbf.v4.new_notebook()
nb2.cells = [
    md("""# 02 — Analysis (Run-All, no API key needed)

Recomputes **every number and figure in the paper** from the frozen CSVs.
Works locally (repo checkout) or on Google Colab (clones the public repo).
"""),
    code(f"""import os, pathlib, sys
if not pathlib.Path('../results/raw_answers.csv').exists() and not pathlib.Path('results/raw_answers.csv').exists():
    # Colab: fetch the public repo
    os.system('git clone {REPO} repo_hfq')
    ROOT = pathlib.Path('repo_hfq')
else:
    ROOT = pathlib.Path('..') if pathlib.Path('../results').exists() else pathlib.Path('.')
sys.path.insert(0, str(ROOT / 'src'))
print('repo root:', ROOT.resolve())"""),
    code("""import importlib, analyze
importlib.reload(analyze)
analyze.main()   # writes metrics_summary.csv, conformal.csv, fsq_table.csv + figures"""),
    md("## Headline tables"),
    code("""import pandas as pd
summary = pd.read_csv(analyze.ROOT / 'results' / 'metrics_summary.csv')
summary.pivot_table(index=['model','setting'], columns='metric', values='value').round(3)"""),
    code("pd.read_csv(analyze.ROOT / 'results' / 'conformal.csv').round(3)"),
    code("pd.read_csv(analyze.ROOT / 'results' / 'fsq_table.csv').round(3)"),
    md("## Figures"),
    code("""from IPython.display import Image, display
for p in sorted((analyze.ROOT / 'results' / 'figures').glob('*.png')):
    print(p.name); display(Image(str(p)))"""),
]
nbf.write(nb2, NB / "02_analysis.ipynb")
print("notebooks written:", [p.name for p in NB.glob("*.ipynb")])
