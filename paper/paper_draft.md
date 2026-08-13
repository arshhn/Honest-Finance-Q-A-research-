# When Should a Finance AI Stay Silent? Selective Answering for Financial-Filings QA, Measured Honestly

**Author:** araa (independent researcher)
**Status: DRAFT v1.1 — post internal-review revision (rulebook v1.8); every number recomputed from frozen CSVs by `notebooks/02_analysis.ipynb`; author's 30-grade human audit pending before submission.**

## Abstract

Large language models answer questions about SEC filings well enough to be tempting and badly enough to be dangerous — so the deployment question is not "how accurate is the model?" but "when should it be allowed to answer at all?" We measure selective answering end-to-end on expert-written filings QA with three tiers of one frontier model family (Claude Haiku 4.5, Sonnet 5, Opus 5) on FinanceBench (150 questions; oracle-evidence and closed-book settings) and a seeded 40-item FailSafeQA subset, comparing three practical confidence signals — (M1) verbalized 0–100 confidence, (M2) paraphrase self-agreement, (M3) a judge-free evidence-presence check — under a pre-registered, frozen-output protocol with held-out threshold calibration. Four findings. **(1)** With gold evidence and an explicit "CANNOT ANSWER" option, error among answered questions is already 7.7–10.1% *before any thresholding*: at a 10% risk target, tuned confidence thresholds turn out to bind almost nothing — the models' own refusals do the work — and whether the target is met on a held-out half depends on the split (met in 49–88% of 200 random splits). **(2)** Decontaminated self-agreement is the most *reliable* rule we test: for the small tier it meets the 10% target in 98.5% of splits at ~84% coverage. **(3)** Nothing is certifiable: a rule that demands a finite-sample statistical bound (exact binomial, 95%) before answering certifies zero coverage at either 5% or 10% with a 75-question calibration set — a concrete measurement of how much calibration data risk-*guaranteed* filings QA actually needs. **(4)** On perturbed FailSafeQA items with the abstention option present, fabrication on unanswerable inputs was 0/118 pooled (exact 95% upper bound 2.5%) while 82.5–90% of perturbed-answerable items were still answered correctly — a striking contrast, though not a causal one, with the 41% fabrication the FailSafeQA authors report for the most robust model under their protocol. All raw outputs were frozen before analysis; the design, every mid-course deviation, and this revision are logged in a version-controlled rulebook.

## 1. Introduction

Financial-filings QA has a measured honesty problem. FinanceBench found GPT-4-Turbo with retrieval incorrectly answered or refused 81% of questions (Islam et al., 2023); FailSafeQA reports its most robust frontier model fabricating answers on 41% of perturbed or context-degraded inputs while the most compliant over-refuses (Kamble et al., 2025); FinTrust (2025) reports overconfidence on unanswerable financial questions. Regulated deployment needs an *operating rule*: answer only when a confidence signal clears a threshold chosen to keep the error rate among answers below a target.

Selective prediction supplies the machinery. To our knowledge — from a 107-paper limitations review (§2) re-verified by a fresh sweep in August 2026 — no published study applies risk-targeted selective answering to financial-filings QA benchmarks; the nearest neighbours are COIN (general-domain selective QA with FDR control; AAAI 2026), A-CRC-QA (general-domain asymptotic risk control; Aug 2026), and FinAbstain (conformal abstention for financial *forecasting*, simulated evaluation; Jul 2026). We supply the missing measurement, deliberately isolated from retrieval: models receive the gold evidence pages, so every failure is a failure of *knowing when not to answer*.

Contributions: **(1)** the first pre-specified, frozen-output measurement of what selective answering buys on expert-written filings QA, across three capability tiers and three deployable signals, with the operating points a compliance team would actually use; **(2)** an honest account of the statistics: plug-in thresholds vs. certified (exact-bound) thresholds, split-sensitivity over 200 seeds, and the negative result that finite-sample certification is impossible at n≈75 calibration questions; **(3)** evidence that with an explicit abstention affordance, fabrication on unanswerable perturbed inputs is at most 2.5% pooled (95% upper bound) at our scale, alongside a candid list of confounds that prevent a causal comparison with prior benchmark reports; **(4)** a fully reproducible artifact: pre-registered rulebook with a complete deviation log (including an adversarial internal review that reshaped this draft), frozen raw outputs, and a no-API-key Run-All notebook.

## 2. Related work

**Benchmarks that measure the failure.** FinanceBench (Islam et al., 2023): 150 expert questions over SEC filings with gold evidence; documented the refusal-vs-hallucination trade-off. FailSafeQA (Kamble et al., 2025): query and context perturbations over long filings, scoring robustness against compliance with an LLM judge. FinTrust (2025); FinVerBench (2026): calibration-adjacent findings on financial tasks. Our 107-paper review tags hallucination/abstention as a stated limitation in ~20 papers; FinRAG-12B (2026) fine-tunes for refusals in retail banking without risk targets.

**Selective prediction and risk control.** Verbalized confidence (Lin et al., 2022; Tian et al., 2023), self-consistency (Wang et al., 2023), risk–coverage analysis (Geifman & El-Yaniv, 2017), conformal risk control (Angelopoulos et al., 2022), and provable selective QA (COIN, 2026; A-CRC-QA, 2026) are established outside finance. We do not extend this methodology; we measure what it delivers on filings QA, including where its guarantees are vacuous at realistic calibration sizes.

## 3. Method

### 3.1 Data
- **FinanceBench open set**: 150 questions (50 metrics-generated / 50 domain-relevant / 50 novel-generated; 32 companies; up to 7 questions share a filing — a clustering limitation, §6). *Oracle-evidence*: gold evidence pages provided. *Closed-book*: no document.
- **FailSafeQA**: seeded subset of 40/220 items (seed 20260807; quota-forced scope cut, logged before any run). Per item, 3 conditions: **base** (clean query + full filing, ~32k tokens); one **perturbed-answerable** rotated over {misspelled, incomplete, out-of-domain rephrase, OCR-corrupted context}; one **unanswerable** rotated over {context removed, out-of-scope query}.

### 3.2 Models and protocol
Claude Haiku 4.5 / Sonnet 5 / Opus 5, accessed through the Claude Code agent harness (subscription path; the pre-registered API path was unaffordable), reasoning effort pinned to "medium". One item-level ask protocol throughout: answer only from the provided document; reply exactly "CANNOT ANSWER" if it lacks the information; output `ANSWER:` + `CONFIDENCE: <0–100>`. Items were delivered under two packing regimes: one-per-sitting (605 sittings) and multi-item exam papers (FinanceBench papers: mean 9.8 items, max 12; FailSafeQA papers: mean 2.3, max 3) with an explicit item-independence header — adopted mid-run when per-question harness overhead consumed >95% of tokens; both the switch and its risks are logged (rulebook v1.3/v1.5) and probed in §4.6. The harness wrapper means the measured system is "model + fixed thin agent scaffold", not a bare API call (§6).

### 3.3 Confidence signals
- **M1 — verbalized confidence**: the stated integer. Defined on all questions.
- **M2 — paraphrase self-agreement**: each question paraphrased once (pinned prompt, frozen pre-run); signal = the two answers agree (numeric within 1%; text via pinned same-answer judge); refusal on either side = disagree. **Scope correction (v1.8):** 117/450 pairs had both askings inside one exam paper, breaking independence; they are excluded. Valid pairs: 112 (Haiku), 112 (Sonnet), 109 (Opus); M2 metrics use this eligible population.
- **M3 — evidence-presence check**: judge-free string check — does the answer's number appear in the evidence after normalising commas, currency, parenthesised negatives, percents, ×10³/×10⁶ re-expressions? Per pre-registration, defined only on numeric-gold oracle questions (n=53 per tier; an earlier all-questions computation was a scope bug, corrected in v1.8).

### 3.4 Grading
Numeric-gold questions (433 rows): deterministic parser — 1% relative tolerance in the question's stated unit, plus half a unit in the gold's last printed decimal; clean power-of-ten mismatches flagged as scale errors and graded wrong. Text-gold questions (966 rows): pinned AI grader (mid tier). Refusals (191) and unanswerable-condition rows (118) detected deterministically. The 61 parser-incorrect rows also received a grader second opinion; 4 disagreed. Audit: the large tier re-graded 63 grades (60 seeded random — of which one coincided with a disagreement row — plus the remaining flagged rows): overall agreement 59/63 (93.7%, Cohen's κ 0.78); random-sample agreement 59/60. All 4 disagreements were resolved against the parser by both AI graders and adjudicated to the majority verdict; because this second-opinion pipeline only re-examines parser-*incorrect* rows it can only raise accuracy, so §4.4 reports pre- and post-adjudication results side by side. A 10-question pilot was hand-audited in full before the main runs (one grader fix, logged). The author's independent 30-grade hand audit is pending and gates submission.

### 3.5 Operating rules (plug-in and certified)
Graded oracle answers are split 50/50 by question (primary seed 20260807) into tuning and proving halves. **Plug-in rule (pre-registered):** smallest threshold *t* whose tuning-half empirical selective risk ≤ target. **Certified rule (added in v1.8):** smallest *t* whose one-sided 95% exact (Clopper-Pearson) upper bound on tuning-half risk ≤ target — the finite-sample-safe analogue. Chosen rules are applied untouched to the proving half; we report coverage, n answered, realized risk, and exact 95% intervals; rows with n<20 answered are flagged degenerate. Split-sensitivity: the entire procedure re-run over 200 random splits. We do not use the word *guarantee* for the plug-in rule.

## 4. Results

n=150 questions per tier per setting (FinanceBench); FailSafeQA sittings 118 (Haiku; both lost sittings were out-of-scope items) / 120 / 120. Accuracies carry exact 95% CIs in brackets.

### 4.1 Accuracy, refusal, and the closed-book gap

| | Haiku 4.5 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| Oracle accuracy (all 150) | 82.7% [75.6, 88.4] | 88.0% [81.7, 92.7] | 91.3% [85.6, 95.3] |
| Oracle accuracy (among answered) | 89.9% | 92.3% | 91.9% |
| Oracle refusal rate | 8.0% | 4.7% | 0.7% |
| Closed-book accuracy | 18.7% [12.8, 25.8] | 44.7% [36.6, 53.0] | 68.7% [60.6, 76.0] |
| Closed-book refusal rate | 54.0% | 28.0% | 10.0% |

Accuracy rises with tier and refusal falls, but the Sonnet–Opus accuracy gap is within paired noise at n=150, and the *signal-quality* ordering is not monotonic (§4.2–4.3) — we therefore do not claim a clean capability ladder. Scale errors (the classic ×1000 slip): zero in the oracle setting; exactly one in the whole study (Haiku, closed-book). The closed-book results show substantial memorised knowledge of these filings (up to 68.7%), which inflates confidence–correctness alignment in unquantified ways: all oracle-setting numbers should be read as *for questions partially familiar from pretraining* (§6).

### 4.2 What each signal offers (full-sample operating points)

On eligible populations: M1 (all 150), M2 (valid pairs 112/112/109), M3 (numeric-gold, 53).

| Signal | Haiku | Sonnet | Opus |
|---|---|---|---|
| M1: matched-coverage mean risk (cov 0.2–0.9) | 4.7% | 4.6% | 3.3% |
| M1: in-sample coverage at ≤10% risk | 90.0% | 95.3% | 99.3% |
| M1: in-sample coverage at ≤5% risk | 78.0% | 80.7% | 86.7% |
| M2: coverage / risk | 83.9% / 5.3% | 82.1% / 7.6% | 93.6% / 8.8% |
| M3: coverage / risk | 83.0% / 11.4% | 81.1% / 7.0% | 81.1% / 7.0% |

In-sample coverages are maximally-selected statistics and overstate what a deployed rule achieves — §4.4 gives the held-out picture. M3, restricted to its defined scope, is the weakest and noisiest signal (n=53).

### 4.3 Calibration

Decile-bin ECE on answered questions: 4.6% (Haiku, n=138), 9.4% (Sonnet, n=143), 4.3% (Opus, n=149). Reliability diagrams are near-diagonal in aggregate, but individual bins are small and noisy — e.g. Haiku's [80,90) bin holds 16 answers at 56% accuracy — so we claim aggregate calibration only, note that ECE at n≈150 is bin-sensitive, and observe that the *mid* tier is the worst-calibrated of the three. Relative to the systematic overconfidence reported on earlier model generations, these are small errors; they are not bin-level reliability.

### 4.4 Held-out operating points, certification, and split-sensitivity

Primary seed (20260807), plug-in rule:

| Model | Signal | Target | Coverage | n ans. | Realized risk [95% CI] | Note |
|---|---|---|---|---|---|---|
| Haiku | M1 | 10% | 94.7% | 71 | 11.3% [5.0, 21.0] | threshold excluded 0 answers |
| Sonnet | M1 | 10% | 98.7% | 74 | 6.8% [2.2, 15.1] | threshold excluded 0 answers |
| Opus | M1 | 10% | 100.0% | 75 | 8.0% [3.0, 16.6] | threshold excluded 0 answers |
| Haiku | M2 | 10% | 85.2% | 46 | 2.2% [0.1, 11.5] | |
| Sonnet | M2 | 10% | 90.7% | 49 | 6.1% [1.3, 16.9] | |
| Opus | M2 | 10% | 94.2% | 49 | 8.2% [2.3, 19.6] | |
| Haiku | M1 | 5% | 18.7% | 14 | 0.0% [0.0, 23.2] | degenerate (n<20) |
| Sonnet | M1 | 5% | 4.0% | 3 | 0.0% [0.0, 70.8] | degenerate |
| Opus | M1 | 5% | 2.7% | 2 | 0.0% [0.0, 84.2] | degenerate |

Three honest readings. **(a) At 10%, the thresholds are inert.** For all three tiers the selected M1 threshold excludes zero additional answers on the proving half: coverage equals the non-refusal rate, and the achieved risk is the model's native error-among-answered. The models' built-in refusal behaviour already sits at the 10% boundary; thresholding adds nothing there. **(b) At 5%, plug-in thresholds certify nothing usable.** The surviving operating points answer 2–14 questions; their intervals extend to 23–84%. **(c) The certified rule certifies nothing at all.** Requiring an exact 95% upper bound ≤ target on the tuning half yields zero answerable coverage for every tier at both targets: with 75 calibration questions, ~0 errors in ~30+ answered tuning items would be needed. Risk-*guaranteed* selective filings QA needs a calibration set several times larger than half of FinanceBench — a concrete design requirement for future benchmarks.

**Split-sensitivity (200 random splits, plug-in):** M1@10% meets the target in 49% (Haiku), 87.5% (Sonnet), 86% (Opus) of splits — for the small tier it is a coin flip. M2@10% meets it in 98.5% (Haiku), 62.5% (Sonnet), 37.5% (Opus) of splits at median coverage 84/82/93% — making decontaminated self-agreement the most reliable 10% rule for the small tier, while for the large tier simply *answering everything it doesn't refuse* is as defensible as any rule tested. M1@5% meets the target in only 43–64% of splits. **Adjudication sensitivity:** under the pre-adjudication grades, the only headline row that changes is Sonnet M1@10% (coverage 86.7%, realized 4.6% [1.0, 12.9]); Haiku and Opus rows are identical.

### 4.5 FailSafeQA: guessing when you shouldn't

| | Haiku | Sonnet | Opus |
|---|---|---|---|
| Base accuracy (n=40) | 85.0% | 90.0% | 95.0% |
| Base refusal (over-refusal cost) | 2/40 | 2/40 | 0/40 |
| Robustness: perturbed-answerable acc. (n=40) | 82.5% [67.2, –] | 87.5% [73.2, –] | 90.0% [76.3, –] |
| Compliance: refusal on unanswerable | 38/38 | 40/40 | 40/40 |
| Fabrication (95% exact upper bound) | 0% (≤7.6%) | 0% (≤7.2%) | 0% (≤7.2%) |

Pooled across tiers: **0/118 fabrications, exact 95% upper bound 2.5%.** Robustness costs 2.5–5 points versus clean baseline (differences within paired noise at n=40), and the small over-refusal cost (2/40 clean items refused by the smaller tiers) is the compliance side's price. Per-variant cells (n=8–12) are reported in `results/fsq_table.csv` as indicative only and we draw no per-variant conclusions. **Cross-study contrast, stated carefully:** the FailSafeQA authors report their most robust model fabricating on 41% of perturbed/degraded inputs. Our 0/118 was obtained with different models, a different prompt that makes abstention an explicit legitimate output, a different (non-LLM-judge) scoring protocol, and a 40-item subset — so we report the contrast as motivation for a controlled experiment, not as a causal finding. The pre-registered next step is a no-abstention-instruction control arm on the same items.

### 4.6 Protocol equivalence and instrument validity

Batching equivalence (pre-registered n=30; 26 pairs mapped, 4 attrition; mid tier, oracle only): refusal 1/26 vs 1/26; mean confidence 80.7 (batched) vs 82.8 (single); numeric-arm accuracy 9/10 vs 9/10; 9/10 numeric answers identical within 1%. These are consistent with equivalence but underpowered to establish it; batching remains a disclosed threat (§6). Grading validity rests on: deterministic parsing for all numeric golds, 93.7% cross-tier audit agreement (κ 0.78), the 10-question hand-audited pilot, and the pending author audit — with the caveat that both AI graders share the subjects' model family.

## 5. Discussion

What should a deployer take away? **First, the abstention affordance is doing most of the visible work.** With gold evidence and permission to refuse, these models' unthresholded error-among-answered already sits at 7.7–10.1%, their refusals absorb the worst inputs, and on unanswerable perturbed inputs fabrication was undetected at our scale (≤2.5% pooled, 95% bound). **Second, signal choice matters most below the native operating point.** Confidence thresholds bind only for targets stricter than ~10%; there, nothing we tested is reliable — the honest statement is that 5%-risk filings QA at useful coverage is currently *unverifiable*, not merely unachieved, because certification itself fails at these calibration sizes. **Third, self-agreement earned its cost for the small tier** (98.5% split-reliability at 84% coverage), suggesting a practical recipe: small model + paraphrase re-ask ≈ large model's native reliability at a fraction of the price. These are measurements under one family, one prompt, and modest n; their value is the pre-registered, reproducible baseline they set — including for our companion work on XBRL-anchored verification, which targets exactly the sub-10% regime where every signal here runs out.

## 6. Limitations

Single model family; cross-vendor generality untested. Subjects ran inside an agent harness (thin scaffold, file-read step, pinned "medium" effort) rather than bare API calls; the pre-registered API path was unaffordable, and harness identifiability is a real reproducibility cost. Most sittings shared context windows with other items (equivalence-checked only at n=26, one tier). Token-likelihood baselines (sequence logprob, p(True)) were unavailable through the harness — a gap versus the standard selective-prediction toolkit. FinanceBench questions cluster within filings/companies; our intervals treat questions as independent. Training-data contamination is substantial (closed-book up to 68.7%) and affects confidence–correctness alignment, not just absolute accuracy. FailSafeQA conclusions rest on a 40-item seeded subset with 2 lost sittings; the fabrication bound is scale-limited (≤2.5% pooled). The AI grader and auditor share the subjects' family; adjudication was one-directional by construction (disclosed, sensitivity reported). One sitting per instance; no stochastic averaging.

## 7. Reproducibility & disclosure

Design pre-registered in `docs/design.md` (rulebook v1.0→v1.8; every deviation logged before use; v1.8 documents the internal adversarial review — 8 independent reviewer/searcher agents — that produced this revision, frozen at `docs/internal_review_2026-08-13.md`). Raw outputs frozen to `results/raw_answers.csv`; grades to `results/grades.csv` (frozen) and `results/grades_final.csv` (post-adjudication; analysis default); `notebooks/02_analysis.ipynb` recomputes every number and figure with no API key (Colab-compatible). Pipeline built and executed with AI assistance (Claude); the author directs design, approves stages, and audits grades. Code, data, results: github.com/arshhn/honest-finance-qa.

## References

Angelopoulos, A. et al. (2022). Conformal Risk Control. arXiv:2208.02814.
Geifman, Y., El-Yaniv, R. (2017). Selective Prediction. NeurIPS.
Islam, P. et al. (2023). FinanceBench. arXiv:2311.11944.
Kamble, K. et al. (2025). Expect the Unexpected: FailSafe Long Context QA for Finance. arXiv:2502.06329.
Lin, S. et al. (2022). Teaching Models to Express Their Uncertainty in Words. TMLR.
Tian, K. et al. (2023). Just Ask for Calibration. EMNLP.
Wang, X. et al. (2023). Self-Consistency Improves Chain of Thought Reasoning. ICLR.
COIN (2026). arXiv:2506.20178 (AAAI 2026). A-CRC-QA (2026). arXiv:2608.12008. FinAbstain (2026). arXiv:2607.24875.
FinTrust (2025). arXiv:2510.15232. FinVerBench (2026). arXiv:2605.29586. FinRAG-12B (2026). arXiv:2605.05482.
