# CLAUDE.md — project briefing (read me first)

## Who you're working with
araa — solo researcher, beginner-friendly explanations required. Teaching style that works: everyday scene first, technical term last, ONE concept at a time (the established analogies: AI = student in closed-book exam; hallucination = confident guessing; RAG = open-book exam; chunks = book cut into pieces; retrieval = librarian; embeddings = meaning-addresses; XBRL = invisible barcode stickers on every number: what/who/when/unit; abstention = honest "I don't know"; calibration = the weather-man test). Do NOT dump jargon. araa makes decisions and audits; you (Claude) write and run all code. araa's guide must be able to see reproducible work: keep every analysis runnable top-to-bottom from frozen CSVs in Colab-compatible notebooks, no API keys required for analysis.

## The research (2 papers, 5-day sprint; Day 1 nearly done)
Backstory: we reviewed 107 papers on RAG/LLM QA over financial filings and adversarially verified a gap (full analyses in docs/gap_analysis_107papers.md). 
- **Paper 1 (Days 1–3): "calibrated abstention for filings QA."** Measure when models should refuse to answer. Datasets: FinanceBench open-150 (in data/financebench.csv; oracle-evidence setting + closed-book control) and FailSafeQA (HuggingFace `Writer/FailSafeQA` — downloadable directly now). 3 Claude tiers as subjects; confidence signals M1 verbalized 0–100, M2 paraphrase self-agreement, M3 judge-free evidence-presence check; split-conformal threshold (tune half → prove half, seeded); outputs: risk–coverage curves, coverage@5%/10% risk, calibration plots, FailSafeQA robustness-vs-compliance table. FULL RULEBOOK: docs/design.md — treat it as binding; log any change in its changelog.
- **Paper 2 (Days 4–5 start): "XBRL-anchored verification layer."** The verified gap: no credible peer-reviewed system uses inline-XBRL anchors (concept/period/entity/unit tags on every statement number) as retrieval-filtering + numeric-verification + per-number-citation + abstention substrate for narrative filings QA. Nearest neighbors to cite & differentiate: LEDGER (2606.13100, XBRL as ground truth only), FinTagging (2505.20650), AuditFlow (2606.03031, structured audit), FinReporting (2604.05966), Rafanan et al. IEEE 2026 (XBRL ingestion-only, paywalled), Red Hat agentic-graphrag-finance OSS (July 2026, unpublished), one low-credibility JACS 2023 paper (scipublication.com — cite, differentiate, distrust). Plan: EDGAR companyfacts via edgartools for the 32 FinanceBench companies; link chunks→facts by value+unit+scale+period; verify/cite/abstain layer; before/after on FinanceBench-150. Filing PDFs: clone github.com/patronus-ai/financebench (1.3GB, includes 368 PDFs + the question JSONLs) — deliberately not committed here.

## Current state (PAPER 1 COMPLETE pending araa's audits — supersedes everything below)
- Data collection, grading, adjudication, analysis, figures, notebooks, and the full paper draft are DONE (rulebook v1.7; $0 spent — everything ran through the Claude Code harness across quota windows).
- Headline: 10%-risk selective answering works at 94.7–100% coverage on all 3 tiers; 5%-risk collapses to near-certainty coverage; 100% compliance / 0% fabrication on FailSafeQA-subset unanswerables with the explicit CANNOT-ANSWER protocol.
- paper/paper_draft.md is v1.0. notebooks/02_analysis.ipynb executes end-to-end from frozen CSVs (verified, 0 errors).
- BEFORE SUBMISSION araa must: (1) hand-audit 30 grades (sample from results/grades_final.csv joined to raw_answers.csv), (2) verify 5 paper numbers against the notebook, (3) rotate the API key in .env (pasted in chat once), (4) read paper + changelog end-to-end.
- Paper 2 (XBRL-anchored verification) not started.

## Old state (historical)
- araa granted blanket approval for the full research on 2026-08-07 ("all my approvals for everything").
- FailSafeQA downloaded + frozen (220 items, data/failsafeqa_raw.jsonl + .csv); design.md at v1.2 (full pre-registration — READ THE CHANGELOG before touching anything).
- Full pipeline built and mock-validated end-to-end in src/: prep_instances → run_pilot → run_paraphrases → run_batches (Message Batches API) → freeze_raw → grade_all → analyze (+ gen_notebooks). test_grade_lib.py all pass.
- API key in .env (gitignored). BLOCKER at build time: account had zero credits; araa asked to top up (~$150). Background probe polls every 5 min; when live: pilot → paraphrases → prep --with-para → submit batches → collect → freeze → grade → analyze → fill paper/paper_draft.md [PENDING] sections → execute 02_analysis.ipynb → commit+push.
- results/batch_requests/ + batch_raw/ are gitignored (regenerable, ~210MB). Frozen CSVs in results/ are sacred (hard rule 1).

## Original Day-1 state (historical)
- data/financebench.csv — verified: 150 rows, 3 types ×50, 32 companies, no empty Q/A.
- docs/design.md — rulebook v1.0 DELIVERED, awaiting araa's explicit "approved". Do not run full experiments before approval.
- docs/samples_for_you.md — 5 sample questions delivered; awaiting araa's "data ok".
- FailSafeQA not yet downloaded (was blocked in cloud; works here): `load_dataset("Writer/FailSafeQA")`, freeze to data/failsafeqa.csv, record exact row counts in design.md changelog.
- Pilot (Day 1 step 9) NOT yet run: 10 questions × 1 model end-to-end → results/pilot.csv (question, answer, confidence, grade) + mini curve → araa audits all 10 grades (step 10) before Day 2 scale-up.
- Nothing in results/ or notebooks/ yet. GitHub repo `honest-finance-qa` created by araa (this working copy should be pushed there; commit daily).

## Day 2–3 recipe (agreed)
Day 2: full runs 150×3 models×methods + FailSafeQA subset (~250–300) → freeze results/raw_answers.csv IMMEDIATELY per row; grading pass (numeric parser w/ 1% tolerance + scale-error logging; AI grader for text; pin grader prompt in code); 30-grade human audit by araa → agreement % goes in paper. Day 3: seeded 50/50 conformal split; threshold on tune half at 5% & 10% targets; report realized risk on prove half w/ 1000-bootstrap CI; figures (risk–coverage per model×method; calibration); FailSafeQA robustness table; draft 4–6pp paper (related work source: docs/gap_analysis_107papers.md); notebooks/01_runs.ipynb + 02_analysis.ipynb must Run-All from frozen CSVs; araa verifies 5 numbers by hand; arXiv package (araa submits; first-timer may need endorsement — guide can endorse).

## Hard rules
1. Frozen raw outputs are sacred — analysis only ever reads the CSVs. 2. No rule changes after results without changelog entry. 3. Human audit before trusting any AI grader (they're too generous — FinForge: judge 100% vs experts 70%). 4. Quotes from papers <15 words. 5. Disclose AI-assisted pipeline in the paper. 6. Any step running >2× budget → cut scope (fewer questions/methods), never slip days.
