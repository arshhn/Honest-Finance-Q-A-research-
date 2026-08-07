# When Should a Finance AI Stay Silent? Calibrated Abstention for Financial-Filings QA

**Author:** araa (independent researcher)
**Status: DRAFT — results sections marked [PENDING] are filled from frozen results; do not cite until v1.0.**

## Abstract

Large language models answer questions about SEC filings well enough to be tempting and badly enough to be dangerous: on FinanceBench-style tasks, frontier models still return wrong numbers with high stated confidence, and on perturbed inputs the most robust models fabricate answers in up to 41% of cases (FailSafeQA). We ask a deployment-shaped question: *if a model only answers when a confidence signal clears a threshold, how much can it answer while keeping the error rate among its answers below a target?* We evaluate three Claude model tiers on FinanceBench (150 expert questions, oracle-evidence setting plus a closed-book control) and FailSafeQA (220 items; perturbed-answerable and unanswerable conditions), comparing three confidence signals — (M1) verbalized 0–100 confidence, (M2) paraphrase self-agreement, and (M3) a judge-free evidence-presence check — under a split-conformal threshold rule tuned on half the questions and evaluated untouched on the other half, with bootstrap confidence intervals. [PENDING: one-sentence headline result.] All raw model outputs are frozen before analysis; every number in this paper is recomputed by a public Run-All notebook from the frozen CSVs.

## 1. Introduction

Financial-filings QA has a measured, persistent honesty problem. FinanceBench found GPT-4-Turbo with retrieval incorrectly answered or refused 81% of questions (Islam et al., 2023); FailSafeQA found the most *robust* frontier model fabricates answers on 41% of perturbed or context-degraded inputs, while the most *compliant* model over-refuses (Kamble et al., 2025); FinTrust reports every tested model is overconfident on unanswerable questions (2025). In a domain where a misread fiscal period or a ×1000 scale slip changes an investment decision, the deployment question is not "how accurate is the model?" but "**when should it be allowed to answer at all?**"

Selective prediction — answering only above a confidence threshold, with a statistical guarantee on the error rate among answers — is the standard machinery for this, yet a 107-paper review of RAG/LLM QA over financial documents (see §2) finds no published study of calibrated abstention with risk guarantees on filings QA. This paper supplies that study, deliberately isolated from retrieval: models receive the gold evidence (oracle setting), so every failure is a failure of *knowing when not to answer*, not of finding the page.

Contributions:
1. A three-way comparison of practical confidence signals (verbalized confidence; paraphrase self-agreement; a cheap, judge-free evidence-presence check specific to numeric finance answers) across three model capability tiers.
2. Split-conformal risk-controlled operating thresholds at 5% and 10% target risk, with realized-risk bootstrap intervals on a held-out half — an operating rule a compliance team could adopt verbatim.
3. A robustness-vs-compliance analysis on FailSafeQA quantifying guessing-when-you-shouldn't, including stated confidence *while* guessing.
4. Full pre-registration (design rulebook with changelog, frozen raw outputs, Run-All reproduction notebook, no API key needed for analysis).

## 2. Related work

**Benchmarks that measure the failure.** FinanceBench (Islam et al., 2023) provides 150 expert-written questions over SEC filings with gold evidence pages and documented the refusal-vs-hallucination trade-off. FailSafeQA (Kamble et al., 2025) perturbs queries (misspellings, incompleteness, out-of-domain rephrasings) and contexts (missing, OCR-corrupted) over long filings and scores robustness against compliance; its headline finding — robustness and compliance trade off sharply — motivates our selective-answering frame. FinTrust (2025) finds universal overconfidence on unanswerable financial questions; FinVerBench (2026) reports 95–100% false-positive rates on clean statements under checklist prompting. Our 107-paper limitations review (repo: `docs/gap_analysis_107papers.md`) tags hallucination/abstention as a stated limitation in ~20 papers and calibrated selective answering as unaddressed in all of them; the closest attempt, FinRAG-12B (2026), fine-tunes for refusals in retail banking but evaluates on 258 examples without risk guarantees.

**Selective prediction and conformal risk control.** Verbalized confidence elicitation (Lin et al., 2022; Tian et al., 2023), self-consistency as a confidence signal (Wang et al., 2023), and selective classification metrics (risk–coverage curves, AURC; Geifman & El-Yaniv, 2017) are established outside finance. Split-conformal calibration of a threshold on held-out data to control selective risk follows the conformal risk control line (Angelopoulos et al., 2022). We apply this machinery, unchanged, where it has not been applied: expert-written filings QA with numeric-scale-aware grading.

**Positioning.** We do not propose a new architecture; we measure whether *existing signals from unmodified frontier models* suffice for risk-controlled deployment on filings QA — the missing baseline that both benchmark papers and system papers implicitly assume.

## 3. Method

### 3.1 Data
- **FinanceBench open set**: 150 questions (50 metrics-generated, 50 domain-relevant, 50 novel-generated; 32 companies). *Oracle-evidence* setting: the model receives the gold evidence page(s) with the question — isolating the answer/abstain decision from retrieval. A *closed-book* control runs the same 150 questions with no document.
- **FailSafeQA**: all 220 items (fixed count logged in the design changelog). Per item we run 3 conditions: (a) **base** — clean query + full filing context; (b) one **perturbed-answerable** condition, rotated deterministically by item index over {misspelled query, incomplete query, out-of-domain rephrasing, OCR-corrupted context} (55 items each); (c) one **unanswerable** condition, rotated over {context removed, out-of-scope query} (110 each). Robustness = accuracy on (b); compliance = refusal rate on (c).

### 3.2 Models and protocol
Three Claude tiers — small (`claude-haiku-4-5`), mid (`claude-sonnet-5`), large (`claude-opus-5`) — called through the provider's batch API at **API-default settings** (no temperature/thinking/effort overrides; the mid and large tiers reason by default, the small tier does not — we treat reasoning-by-default as a property of the tier and disclose it). Exact model snapshot identifiers are recorded in every row of the frozen results. The verbatim ask protocol (one question per request) instructs: answer only from the document, reply exactly "CANNOT ANSWER" if it does not contain enough information, and output `ANSWER:` plus `CONFIDENCE: <0–100>`.

### 3.3 Confidence signals
- **M1 — verbalized confidence**: the stated 0–100 integer.
- **M2 — paraphrase self-agreement**: each question is paraphrased once (pinned prompt, mid-tier model, frozen before runs); the signal is whether the answers to the original and paraphrased question agree (numeric: within 1%; text: a pinned same-answer judge).
- **M3 — evidence-presence check**: judge-free and finance-specific — does the answer's number literally appear in the provided evidence after normalizing commas, currency symbols, parenthesized negatives, percent signs, and ×10³/×10⁶ scale re-expressions? Defined for numeric-gold questions in the oracle setting.

### 3.4 Grading
Numeric-gold questions are graded by a deterministic parser: values compared at 1% relative tolerance **in the question's stated unit** (FinanceBench golds are expressed in question units; candidates may answer with explicit scale words or absolute values — all consistent interpretations are accepted), with clean power-of-ten mismatches flagged as *scale errors* and graded wrong. Text-gold questions are graded by a pinned AI grader (question + gold + candidate → correct/incorrect/refused). Refusals are detected by the exact protocol string plus grader-labelled declines. Grader validity: the large-tier model re-grades a seeded sample of 60 grades plus every parser/grader disagreement; [PENDING: agreement rates]. A 30-grade human audit by the author is [PENDING/reported here].

### 3.5 The guarantee
Graded oracle-setting answers are split 50/50 by question (seed 20260807) into a tuning half and a proving half. On the tuning half we select the smallest threshold *t* whose selective risk (error rate among answered questions with confidence ≥ *t*) is ≤ the target (5% or 10%). Applied untouched to the proving half, we report realized selective risk with a 1,000-resample bootstrap interval; the guarantee "held" if the target lies at or above the realized risk / within the interval. For the binary signals (M2, M3) the rule is "answer only when the signal is positive," tuned/proved the same way.

## 4. Results [PENDING — filled from frozen results/]

### 4.1 Accuracy, refusal, and the closed-book gap
[PENDING: table from metrics_summary.csv]

### 4.2 Risk–coverage: which signal buys the most safe coverage?
[PENDING: figures risk_coverage_{model}.png; AURC; coverage@5%/10%]

### 4.3 Calibration
[PENDING: calibration figures + ECE]

### 4.4 The conformal operating rule
[PENDING: conformal.csv table; which model×method held at which target]

### 4.5 FailSafeQA: guessing when you shouldn't
[PENDING: fsq_table.csv; robustness vs compliance; confidence-while-guessing]

### 4.6 Error anatomy
[PENDING: scale-error rates; refusal-when-evidence-present; qualitative examples]

## 5. Discussion [PENDING]

## 6. Limitations
Single provider (three tiers of one model family); oracle-evidence isolates abstention from retrieval by design (Paper 2 addresses retrieval); one run per instance (API-default stochasticity not averaged); the AI grader shares a model family with the graded systems (mitigated by parser-first routing, cross-tier audit, and human audit); FailSafeQA robustness uses one perturbation per item (balanced rotation) rather than the full cross-product; M3 is defined only for numeric answers with provided evidence.

## 7. Reproducibility & disclosure
All raw model outputs were frozen to CSV before any analysis; `notebooks/02_analysis.ipynb` recomputes every number and figure from the frozen CSVs with no API key (Colab-compatible). The design was pre-registered in `docs/design.md`; every deviation is in its changelog. This research pipeline was built and executed with AI assistance (Claude); the author directed the design, approves each stage, and audits grades by hand.

## References
[PENDING: full list — FinanceBench (arXiv:2311.11944), FailSafeQA (arXiv:2502.06329), FinTrust (arXiv:2510.15232), FinVerBench (arXiv:2605.29586), FinRAG-12B (arXiv:2605.05482), Geifman & El-Yaniv 2017, Angelopoulos et al. 2022, Lin et al. 2022, Tian et al. 2023, Wang et al. 2023.]
