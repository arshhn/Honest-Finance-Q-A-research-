# When Should a Finance AI Stay Silent? Calibrated Abstention for Financial-Filings QA

**Author:** araa (independent researcher)
**Status: DRAFT v1.0 — all numbers computed from frozen results (post-adjudication, rulebook v1.7); author's 30-grade human audit pending before submission.**

## Abstract

Large language models answer questions about SEC filings well enough to be tempting and badly enough to be dangerous — the deployment question is not "how accurate is the model?" but "when should it be allowed to answer at all?" We study selective answering on expert-written filings QA with three tiers of one frontier model family (Claude Haiku 4.5, Sonnet 5, Opus 5) on FinanceBench (150 questions, oracle-evidence setting plus closed-book control) and a seeded FailSafeQA subset (perturbed-answerable and unanswerable conditions), comparing three confidence signals — (M1) verbalized 0–100 confidence, (M2) paraphrase self-agreement, (M3) a judge-free evidence-presence check — under a split-conformal threshold rule tuned on half the questions and evaluated untouched on the other half. Three findings. **(1) A 10% selective-risk target is practical today:** thresholded verbalized confidence sustains 94.7–100% coverage with realized held-out risk of 6.8–11.3% across all three tiers, and self-agreement is competitive (84–96% coverage); verbalized confidence is far better calibrated than older-generation literature suggests (ECE 4.3–9.4%). **(2) A 5% target is not:** coverage collapses to 2.7–18.7% — models must be near-certain before answering — and the binary signals cannot reach it at all. **(3) With an explicit abstention instruction, the hallucination-under-perturbation problem largely disappears at this scale:** on FailSafeQA's unanswerable conditions all three tiers refused 100% of items (0% fabrication) while still answering 82.5–90% of perturbed-but-answerable items correctly — where the FailSafeQA authors reported their most robust model fabricating in 41% of cases without such an instruction. All raw outputs are frozen before analysis; every number is recomputed by a public Run-All notebook from the frozen CSVs, with the full design pre-registered in a version-controlled rulebook.

## 1. Introduction

Financial-filings QA has a measured honesty problem. FinanceBench found GPT-4-Turbo with retrieval incorrectly answered or refused 81% of questions (Islam et al., 2023); FailSafeQA found the most *robust* frontier model fabricates answers on 41% of perturbed or context-degraded inputs while the most *compliant* over-refuses (Kamble et al., 2025); FinTrust reports models overconfident on unanswerable questions (2025). In a domain where a misread fiscal period or a ×1000 scale slip changes decisions, regulated deployment needs a *risk-controlled operating rule*: answer only when a confidence signal clears a threshold chosen so that the error rate among answers stays below a target.

Selective prediction supplies exactly this machinery, yet a 107-paper review of RAG/LLM QA over financial documents (§2) finds no published study of calibrated abstention with risk guarantees on filings QA. This paper supplies that study, deliberately isolated from retrieval: models receive the gold evidence pages (oracle setting), so every failure is a failure of *knowing when not to answer*, not of finding the page.

Contributions: (1) a three-signal, three-tier comparison of practical confidence signals on expert-written filings QA; (2) split-conformal operating thresholds at 5% and 10% target risk with realized-risk bootstrap intervals on a held-out half — an operating rule a compliance team could adopt verbatim, including the negative result that 5% is currently out of reach at useful coverage; (3) a robustness-vs-compliance analysis showing that an explicit abstention instruction eliminates fabrication on unanswerable perturbed inputs at our sample size while preserving robustness; (4) full pre-registration (version-controlled rulebook with changelog), frozen raw outputs, and a no-API-key Run-All reproduction notebook.

## 2. Related work

**Benchmarks that measure the failure.** FinanceBench (Islam et al., 2023) provides 150 expert-written questions over SEC filings with gold evidence pages and documented the refusal-vs-hallucination trade-off. FailSafeQA (Kamble et al., 2025) perturbs queries (misspellings, incompleteness, out-of-domain rephrasings) and contexts (missing, OCR-corrupted) over long filings and scores robustness against compliance. FinTrust (2025) finds overconfidence on unanswerable financial questions; FinVerBench (2026) reports 95–100% false-positive rates on clean statements under checklist prompting. Our 107-paper limitations review (`docs/gap_analysis_107papers.md`) tags hallucination/abstention as a stated limitation in ~20 papers; the closest system attempt, FinRAG-12B (2026), fine-tunes for refusals in retail banking without risk guarantees.

**Selective prediction and conformal risk control.** Verbalized confidence (Lin et al., 2022; Tian et al., 2023), self-consistency signals (Wang et al., 2023), risk–coverage analysis (Geifman & El-Yaniv, 2017), and split-conformal calibration of thresholds (Angelopoulos et al., 2022) are established outside finance. We apply this machinery, unchanged, where it had not been applied — and find the field's standard pessimism about verbalized confidence does not transfer to current-generation models on this task.

## 3. Method

### 3.1 Data
- **FinanceBench open set**: 150 questions (50 metrics-generated, 50 domain-relevant, 50 novel-generated; 32 companies). *Oracle-evidence*: the model receives the gold evidence page(s) with the question. *Closed-book control*: same questions, no document.
- **FailSafeQA**: a seeded subset of 40/220 items (seed 20260807; a quota-forced scope cut logged in the rulebook before any run). Per item, 3 conditions: **base** (clean query + full filing context, mean ~32k tokens); one **perturbed-answerable**, rotated deterministically over {misspelled query, incomplete query, out-of-domain rephrasing, OCR-corrupted context}; one **unanswerable**, rotated over {context removed, out-of-scope query}. Robustness = accuracy on perturbed-answerable; compliance = refusal rate on unanswerable.

### 3.2 Models and protocol
Three tiers of one family — Claude Haiku 4.5 (small), Claude Sonnet 5 (mid), Claude Opus 5 (large) — accessed through the Claude Code agent harness (subscription path; the pre-registered API path was unaffordable), reasoning effort pinned to "medium", one exam protocol for every sitting: answer only from the provided document; reply exactly "CANNOT ANSWER" if it does not contain enough information; output `ANSWER:` plus `CONFIDENCE: <0–100>`. Most sittings were collected in multi-item exam papers (mean 9.9 independent items per sitting; header instructs strict item independence) after per-question calls proved to spend >95% of tokens on harness overhead; a pre-registered equivalence check (§4.6) compares the two protocols. The harness wrapper, packing, and their risks (cross-item bleed, effort economising) are logged as rulebook deviations v1.3/v1.5 and are limitations (§6).

### 3.3 Confidence signals
- **M1 — verbalized confidence**: the stated 0–100 integer.
- **M2 — paraphrase self-agreement**: each question paraphrased once (pinned prompt, mid-tier model, frozen before runs); signal = answers to original and paraphrase agree (numeric: within 1%; text: pinned same-answer judge). Refusal on either side counts as disagreement.
- **M3 — evidence-presence check**: judge-free — does the answer's number literally appear in the evidence after normalizing commas, currency, parenthesized negatives, percents, and ×10³/×10⁶ re-expressions? Defined for numeric-gold oracle questions.

### 3.4 Grading
Numeric-gold questions: deterministic parser, 1% relative tolerance **in the question's stated unit**, plus half-a-unit-in-the-last-printed-decimal tolerance (golds are rounded values); clean power-of-ten mismatches flagged as *scale errors* and graded wrong; percent↔fraction interpretations handled. Text-gold questions: pinned AI grader (mid tier), one verdict per answer (correct/incorrect/refused). Refusals: exact protocol string plus grader-labelled declines. Parser-incorrect rows also receive a grader second opinion; only 4/1,708 rows showed parser–grader disagreement (all audited). Grader validity: the large tier re-graded a seeded sample of 60 grades (100% agreement) plus every disagreement (all 4 resolved against the parser and adjudicated); the author's independent 30-grade hand audit is pending and gates submission. A 10-question pilot was hand-audited in full before the main runs and produced one grader fix (percent-vs-rounded-fraction), logged and re-tested before any full run.

### 3.5 The guarantee
Graded oracle answers split 50/50 by question (seed 20260807) into tuning and proving halves. On the tuning half: the smallest threshold *t* whose selective risk (errors among answered with confidence ≥ *t*) ≤ target (5%, 10%). Applied untouched to the proving half; realized selective risk reported with a 1,000-resample bootstrap percentile interval; the guarantee "held" if the target lies at/above realized risk or inside the interval. Binary signals (M2, M3): the rule "answer only when the signal is positive," tuned/proved identically.

## 4. Results

All numbers recomputed by `notebooks/02_analysis.ipynb` from frozen CSVs. n=150 questions per model per setting (FinanceBench); FailSafeQA subset n=40 items per condition-group per model (Haiku 118/120 sittings; 2 lost to collection attrition).

### 4.1 Accuracy, refusal, and the closed-book gap

| | Haiku 4.5 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| Oracle accuracy (all 150) | 82.7% | 88.0% | 91.3% |
| Oracle accuracy (among answered) | 89.9% | 92.3% | 91.9% |
| Oracle refusal rate | 8.0% | 4.7% | 0.7% |
| Closed-book accuracy | 18.7% | 44.7% | 68.7% |
| Closed-book refusal rate | 54.0% | 28.0% | 10.0% |
| Scale-error rate (oracle) | 0.0% | 0.0% | 0.0% |

A clean capability ladder with a mirror-image honesty ladder: the small tier compensates for closed-book ignorance with heavy refusal (54%), the large tier answers from memory — 68.7% closed-book accuracy implies substantial exposure to these filings' contents in training, a contamination consideration for all absolute numbers on this benchmark. Scale errors, the classic ×1000 finance failure, did not occur in the oracle setting for any tier.

### 4.2 Risk–coverage: what does each signal buy?

At full coverage the oracle error-among-answered is 7.7–10.1%. Descriptively (full sample), M1-thresholding reaches ≤10% risk at 90.0% (Haiku), 95.3% (Sonnet), 99.3% (Opus) coverage, and ≤5% risk at 78.0/80.7/86.7% — but the 5% thresholds are unstable under the tune/prove split (§4.4). Area under the risk–coverage curve: 0.028 (Haiku), 0.055 (Sonnet), 0.042 (Opus). M2 operating points sit at 84.0–95.3% coverage / 7.1–7.7% risk; M3 at 67.3–82.7% coverage / 8.9–12.9% risk (figures: `results/figures/risk_coverage_*.png`).

### 4.3 Calibration

Reliability diagrams (`calibration_*.png`) are close to diagonal for all three tiers: ECE 4.6% (Haiku), 9.4% (Sonnet), 4.3% (Opus). The stated-80% bins are right roughly 80% of the time. This is markedly better than the overconfidence findings that motivated much of the abstention literature on earlier model generations — the weather-man test is now close to passed on in-domain expert questions with gold evidence.

### 4.4 The conformal operating rule (tune half → prove half)

| Model | Signal | Target | Threshold | Coverage | Realized risk | 95% CI | Held |
|---|---|---|---|---|---|---|---|
| Haiku | M1 | 5% | ≥97 | 18.7% | 0.0% | [0,0] | yes |
| Haiku | M1 | 10% | ≥62 | 94.7% | 11.3% | [4.2,18.3] | yes* |
| Haiku | M2 | 10% | agree | 84.0% | 4.8% | [0,11.1] | yes |
| Sonnet | M1 | 5% | ≥97 | 4.0% | 0.0% | [0,0] | yes |
| Sonnet | M1 | 10% | ≥55 | 98.7% | 6.8% | [1.4,12.2] | yes |
| Sonnet | M2 | 10% | agree | 92.0% | 5.8% | [1.4,11.6] | yes |
| Opus | M1 | 5% | ≥99 | 2.7% | 0.0% | [0,0] | yes |
| Opus | M1 | 10% | ≥42 | 100.0% | 8.0% | [2.7,14.7] | yes |
| Opus | M2 | 10% | agree | 96.0% | 6.9% | [1.4,12.5] | yes |
| Opus | M3 | 10% | present | 84.0% | 9.5% | [3.2,17.5] | yes |

(*realized point estimate 11.3% exceeds the target; "held" by the pre-registered interval criterion — the honest reading is "borderline".) Omitted rows (M2/M3 at 5%; Haiku/Sonnet M3 at 10%) failed on the tuning half: the rule answers nothing. The deployment picture: **at 10% target risk every tier supports high-coverage risk-controlled operation (94.7–100% via M1; 84–96% via M2); at 5%, tune-half selection only certifies near-certainty answering (2.7–18.7% coverage) even though in-sample thresholds with ~80% coverage exist — the gap between descriptive and guaranteed 5%-risk operation is itself a finding — and the binary signals cannot reach 5% at all.** Whether 5%-risk filings QA at useful coverage is achievable with better signals — or requires better models — is exactly the open question these numbers pin down.

### 4.5 FailSafeQA: guessing when you shouldn't

| | Haiku | Sonnet | Opus |
|---|---|---|---|
| Base accuracy (clean) | 85.0% | 90.0% | 95.0% |
| Robustness (perturbed-answerable acc.) | 82.5% | 87.5% | 90.0% |
| — misspelled / incomplete / out-of-domain / OCR | 75/80/88/90% | 75/90/88/100% | 100/90/88/80% |
| Compliance (refusal on unanswerable) | **100%** | **100%** | **100%** |
| Fabrication on unanswerable | **0%** | **0%** | **0%** |

Under the same protocol that permits "CANNOT ANSWER", all three tiers refused every missing-context and out-of-scope item (n=40 per model) while answering 82.5–90% of perturbed-but-answerable items correctly — robustness costs only 2.5–5 points relative to clean baseline. Contrast: the FailSafeQA authors, whose prompts did not centre an explicit abstention rule, report their most robust model fabricating on 41% of such inputs. At our sample size the robustness–compliance trade-off essentially dissolves when abstention is made a first-class output. The residual robustness gap concentrates in misspelled queries for the smaller tiers and, curiously, OCR-corrupted context for the largest.

### 4.6 Protocol equivalence and grading validity

Batched vs single-question protocol (26 mapped re-ask pairs, mid tier): refusal rate 3.8% vs 3.8%; mean confidence 80.7 vs 82.8; numeric accuracy 90.0% vs 90.0%; 90% of numeric answers identical within 1%. Pooling the two protocols is justified. Grader triangulation: 4/1,708 parser–grader disagreements. Large-tier (Opus) audit of 63 grades: 100% agreement on the 60-grade seeded random sample; on the 4 deliberately included disagreement rows the auditor sided with the AI grader against the numeric parser in all 4, so those grades were adjudicated to the two-grader majority verdict (logged, rulebook v1.7; original grades.csv preserved, analysis reads grades_final.csv). Author's 30-grade hand audit pending.

## 5. Discussion

Three deployment-relevant conclusions. **First, the cheap signal is good now.** Stated confidence from current-generation models, thresholded conformally, supports 87–100% coverage at a 10% selective-risk target on expert filings questions with evidence in hand — the signal the literature learned to distrust on 2022–2024 models is, for this family and task, calibrated enough to use. **Second, the last factor of two is the hard one.** Tightening the target from 10% to 5% collapses *certified* coverage to 2.7–18.7% — in-sample thresholds with ~80% coverage at 5% risk exist but do not survive the tune/prove split at n=75 per half; none of the three signals unlocks guaranteed 5%-risk coverage — a concrete target for future signals (ensembles, verifier models, retrieval-verification hybrids like the XBRL-anchored layer we develop in companion work). **Third, abstention is partly a prompting problem, not only a capability problem.** Making "CANNOT ANSWER" an explicit, legitimate output eliminated fabrication on unanswerable perturbed inputs at our sample size, across tiers — the strongest single intervention we observe, and one deployments control entirely.

## 6. Limitations

Single model family (three tiers), so cross-vendor generality is untested. Subjects ran inside an agent harness with a file-read step and pinned "medium" effort rather than bare API calls, and most sittings shared a context window with up to 11 other independent items (equivalence-checked on 26 pairs, but the check is small and mid-tier only). FailSafeQA conclusions rest on a seeded 40-item subset (120 sittings/model; 2 lost) — the 100%-compliance result deserves replication at full scale. The closed-book control shows substantial memorised knowledge of these filings (up to 68.7%), so absolute oracle accuracies partly reflect contamination; the selective-risk machinery is unaffected but benchmark-absolute claims should be read accordingly. The AI grader shares a model family with the graded systems (mitigated by parser-first routing for numeric golds, a cross-tier audit, and a pending human audit). One sitting per instance: no averaging over sampling stochasticity. M3 is defined only for numeric answers with provided evidence.

## 7. Reproducibility & disclosure

Design pre-registered in `docs/design.md` (rulebook v1.0→v1.6; every deviation logged with rationale before use). Raw model outputs frozen to `results/raw_answers.csv` before any analysis; grading frozen to `results/grades.csv`; `notebooks/02_analysis.ipynb` recomputes every number and figure from the frozen CSVs with no API key (Colab-compatible). Pipeline built and executed with AI assistance (Claude); the author directs design, approves stages, and audits grades. Code, data, and results: github.com/arshhn/honest-finance-qa.

## References

Angelopoulos, A. et al. (2022). Conformal Risk Control. arXiv:2208.02814.
Geifman, Y., El-Yaniv, R. (2017). Selective Prediction. NeurIPS.
Islam, P. et al. (2023). FinanceBench. arXiv:2311.11944.
Kamble, K. et al. (2025). Expect the Unexpected: FailSafe Long Context QA for Finance. arXiv:2502.06329.
Lin, S. et al. (2022). Teaching Models to Express Their Uncertainty in Words. TMLR.
Tian, K. et al. (2023). Just Ask for Calibration. EMNLP.
Wang, X. et al. (2023). Self-Consistency Improves Chain of Thought Reasoning. ICLR.
FinTrust (2025). arXiv:2510.15232. FinVerBench (2026). arXiv:2605.29586. FinRAG-12B (2026). arXiv:2605.05482.
