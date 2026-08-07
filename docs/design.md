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
- v1.2 (2026-08-07, pre-registered BEFORE any full run; araa granted blanket approval and delegated execution): **(a) Access path:** direct Anthropic API via Message Batches (50% pricing). Tiers: small=`claude-haiku-4-5`, mid=`claude-sonnet-5`, large=`claude-opus-5`; the exact snapshot name from each API response is recorded per row. **(b) Params:** every model at its API defaults — no temperature/top_p (rejected by Sonnet 5/Opus 5), no thinking/effort config (Sonnet 5 & Opus 5 default to adaptive thinking; Haiku 4.5 defaults to none — treated as a property of the tier and disclosed); max_tokens=8000, truncations logged and retried once at 16000. **(c) FinanceBench:** oracle evidence = all `evidence_text_full_page` concatenated (deduped); closed-book control on ALL 150 (pinned prompt in src/prompts.py); M2 re-ask uses the paraphrased question with the same oracle evidence. **(d) FailSafeQA protocol fixed:** per item 3 instances — (1) base query+context; (2) one perturbed-answerable rotating by idx%4 over {misspelled query, incomplete query, out-of-domain rephrase, OCR-corrupted context}; (3) one unanswerable rotating by idx%2 over {missing context, out-of-scope query+context}. 660 instances/model, 1980 total. Robustness = accuracy on perturbed-answerable (vs base); Compliance = refusal rate on unanswerable. **(e) Grading:** gold-numeric questions graded by Python parser (1% rel. tolerance; scale-error flag when candidate/gold ratio ≈ 10^±{2,3,6,9} within 2%); text answers by pinned sonnet-5 grader, one call per answer via batch. Refusal = "CANNOT ANSWER" (case-insensitive) in the ANSWER field, plus grader REFUSED label for hedged declines. **(f) M2 agreement:** numeric within 1%; text via pinned YES/NO judge. **(g) M3:** defined for numeric-gold questions in the oracle setting only (normalization: commas, $, %, parenthesized negatives, thousand/million/billion words, x1000/x1e6 scale). **(h) Audit:** araa's 30-grade human audit is REQUIRED before submission and still pending; interim cross-model audit = opus-5 re-grades 60 seeded-sampled answers + every parser/grader disagreement; both agreement rates reported. **(i) Conformal:** seed 20260807, 50/50 split by question; smallest threshold t with tune-half selective risk <= target (5% and 10%); prove-half realized risk with 1000-resample bootstrap percentile CI. **(j) Constraint log:** API account had zero credits at 2026-08-07 pipeline-build time; runs begin when araa adds credits; if available credit < estimated cost, FailSafeQA scope shrinks (fewer items, seeded) per Hard Rule 6 — never the FinanceBench core.
- v1.1 (2026-08-07, local machine): FailSafeQA downloaded directly from Hugging Face (`Writer/FailSafeQA`, file `FAILSAFEQA_benchmark_data-FINAL.jsonl`, 57,008,485 bytes — no manual supply needed after all). **Exact count fixed: 220 items** (the design's "~250–300 subset" estimate is corrected to the full set of 220; the file is a pretty-printed JSON array, not JSONL). Each item = 1 clean query + gold answer + full filing context + gold citations, plus 4 perturbed queries (misspelled, incomplete, out-of-domain rephrase, out-of-scope) and 1 OCR-corrupted context. Raw file frozen at data/failsafeqa_raw.jsonl; flattened to data/failsafeqa.csv (220 rows × 12 columns, zero nulls in query/answer/context, round-trip verified). FinanceBench re-verified after transfer from cloud session: 150 rows, 50×3 question types, 32 companies, 150 unique ids, no empty question/answer/evidence.
