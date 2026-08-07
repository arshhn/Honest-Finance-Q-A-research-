# Rulebook (experiment design) — Paper 1: "When should a finance AI stay silent?"

*Written before any full run. Changes after this point must be logged in the changelog at the bottom.*

## Goal
Measure how well AI models know **when not to answer** questions about financial filings, and produce an operating rule with a mathematical guarantee: "if the model only answers above confidence t, at most 5% of its answers are wrong."

## Data (the exams)
1. **FinanceBench open set** — 150 expert-written questions about real SEC filings (32 companies, answers + gold evidence included; source: patronus-ai/financebench GitHub). Setting: **oracle-evidence** — the model receives the question plus its gold evidence text. Why: this isolates the "should I answer?" decision from retrieval mistakes (retrieval is Paper 2's battle). A small **closed-book control** (no evidence) runs on the same questions for contrast.
2. **FailSafeQA** — the trick exam (perturbed questions; missing/corrupted context) to measure guessing-when-you-shouldn't. Subset of ~250–300 items, exact count fixed once loaded. *(Access note: Hugging Face blocked from workspace; file supplied by hand — see changelog.)*

## Models (the students)
Three Claude tiers (small / mid / large), run directly from the workspace. Exact model snapshot names recorded automatically in every results row at run time.

## The ask protocol (verbatim prompt skeleton)
> You are answering a question about a company's SEC filing. Use ONLY the provided document text.
> Document: {evidence}
> Question: {question}
> Rules: If the document does not contain enough information, reply exactly "CANNOT ANSWER".
> Reply in this format —
> ANSWER: <your answer, with units>
> CONFIDENCE: <integer 0–100, how likely your answer is correct>

## Confidence signals compared
- **M1 — verbalized confidence:** the 0–100 number the model states.
- **M2 — self-agreement:** re-ask with a paraphrased question; signal = whether the two answers agree (numeric answers: within 1%).
- **M3 — evidence-presence check (judge-free):** does the numeric answer literally appear in the provided evidence (after normalizing commas/units/scale ×1000/×1,000,000)? Cheap, finance-specific, no AI grader involved.

## Grading (the answer key)
- Numeric answers: parsed and compared to gold with 1% tolerance, plus unit/scale awareness (a ×1000 mismatch is WRONG, and logged as a scale error).
- Text answers: a separate AI grader (question + gold + candidate → correct / incorrect / refused), prompt pinned in code.
- **Human audit:** 30 random grades hand-checked by the researcher; human–grader agreement reported in the paper. Grader systematically wrong → fixed and fully re-graded (logged).

## Metrics
Accuracy; refusal rate; **risk–coverage curve** per model × confidence method (x = fraction answered, y = error rate among answered); coverage at ≤5% and ≤10% risk; area under the risk–coverage curve; calibration error (said-80% vs was-right-80%); FailSafeQA robustness vs compliance (answers on broken input vs proper refusals).

## The guarantee (conformal step)
Graded answers split 50/50 into a **tuning half** and a **proving half** (split by question, seeded, logged). On the tuning half: smallest threshold t with error ≤ target among answered. Applied untouched to the proving half; we report the realized error with a bootstrap confidence interval (1,000 resamples). Guarantee "held" = target inside the interval.

## Success criteria (written before results)
1. Pipeline completes on ≥140/150 FinanceBench + the FailSafeQA subset for all three models.
2. Conformal target risk holds on the proving half for at least the best model × method.
3. A clear method ranking (M1 vs M2 vs M3) emerges, stable across at least two models.
Any outcome — including "no model achieves useful coverage at 5% risk" — is a publishable finding; that one would say current models cannot be safely deployed at this risk level.

## Honesty & reproducibility
All raw model outputs frozen to CSV before any analysis; analysis notebooks recompute everything from frozen CSVs (Colab-runnable, no keys). AI-assisted pipeline disclosed in the paper. Code + results public at submission.

## Changelog
- v1.0 (Day 1): initial rulebook. HF blocked → FinanceBench via GitHub clone; FailSafeQA supplied manually; EDGAR blocked (Paper-2 concern only, plan B = researcher downloads 32 companyfacts JSONs locally).
- v1.1 (2026-08-07, local machine): FailSafeQA downloaded directly from Hugging Face (`Writer/FailSafeQA`, file `FAILSAFEQA_benchmark_data-FINAL.jsonl`, 57,008,485 bytes — no manual supply needed after all). **Exact count fixed: 220 items** (the design's "~250–300 subset" estimate is corrected to the full set of 220; the file is a pretty-printed JSON array, not JSONL). Each item = 1 clean query + gold answer + full filing context + gold citations, plus 4 perturbed queries (misspelled, incomplete, out-of-domain rephrase, out-of-scope) and 1 OCR-corrupted context. Raw file frozen at data/failsafeqa_raw.jsonl; flattened to data/failsafeqa.csv (220 rows × 12 columns, zero nulls in query/answer/context, round-trip verified). FinanceBench re-verified after transfer from cloud session: 150 rows, 50×3 question types, 32 companies, 150 unique ids, no empty question/answer/evidence.
