# Novelty re-check — 2026-11-06 (pre-submission)

**Claim checked (paper §1):** no published study applies risk-targeted selective answering to financial-filings QA benchmarks. "Risk-targeted" means an answer-or-abstain threshold chosen to meet a stated error rate among answered questions, then tested on held-out questions.

**Verdict:** the claim still holds as of 2026-11-06. The related work, however, was out of date: several close papers appeared after the 2026-08-13 sweep, and three that the internal review had flagged (2606.29054, 2607.04430, 2608.06532) were never added to the paper. Paper draft v1.2 (rulebook v1.8.3) fixes this.

## Method

- **Web search:** 5 extended searches combining selective answering, abstention, risk control and conformal methods with FinanceBench, FailSafeQA, SEC filings and 10-K.
- **Semantic Scholar citation lists**, fetched 2026-11-06. Papers dated 2026-06-01 or later were kept, then filtered by title and abstract terms.
  - For FinanceBench and FailSafeQA, a broad term list: abstention, selective, conformal, risk control, calibration, refusal, uncertainty, confidence, coverage, hallucination, unanswerable.
  - For the other filings-based benchmarks, a strict list: abstention, selective prediction/answering, conformal, risk control, refusal, unanswerable.

  | Benchmark | Citing papers | Since 2026-06-01 | Matched terms |
  |---|---|---|---|
  | FinanceBench | 358 | 125 | 39 |
  | FailSafeQA | 8 | 2 | 1 |
  | FinQA | 960 | 252 | 16 |
  | TAT-QA | 771 | 167 | 8 |
  | ConvFinQA | 324 | 80 | 4 |
  | DocFinQA | 105 | 31 | 0 |

- **arXiv API abstract searches**, newest first:
  - FinanceBench; FailSafeQA; "financial" combined with abstention or conformal terms; SEC filings, 10-K or annual reports combined with abstention, conformal, refusal or calibration terms (all since 2026-06-01).
  - FinQA, TAT-QA, ConvFinQA or DocFinQA combined with abstention or risk-control terms (since 2026-01-01).
- **Reading:** 28 candidates in total. 4 were read in full (2608.13706, 2608.06532, 2607.18102, 2610.08322); the other 24 were judged from their abstracts.

## Closest work (now cited in §1–§2)

| Paper | What it does | Why it does not meet the claim |
|---|---|---|
| Jin et al., arXiv:2609.20110 (2026-09-17) | Conformal risk control at an error target under 10% for key-value fields that VLMs extract from invoices and forms. Native verbalized confidence clears only 0.1–7.0% of fields under the target. | Document field extraction, not filings QA. |
| Khanmohammadi et al., arXiv:2608.06532 (2026-08-06) | Error-budget "safe yield" at 5% and 20% on financial chart and document-image VQA (FinMME, FinChart-Bench, MME-Finance). Pooled 5% safe yield is near zero. Includes a rephrasing-ensemble confidence signal. | Charts and document images, not filing text. Thresholds are fitted on the evaluation data, with no held-out calibration. |
| VeriFin, Hall et al., arXiv:2608.10213 (2026-08-10) | Checks numeric answers against XBRL facts with the Z3 SMT solver, then accepts, rejects or abstains. Reports 100% observed precision among accepted answers on XBRLFiling (600), FinanceBench (67) and TAT-DQA (403). | Selective answering on filings QA, but with no error target and no confidence thresholds. Also directly relevant to the planned companion paper, which is assessed in a separate check. |
| CLAIR-Fin, arXiv:2608.13706 (2026-08-13) | Multi-agent QA over a central bank's annual report (BB-FinQA-X, 500 questions). Abstains by a fixed claim-audit rule (27/500 abstained). | No error target, no risk–coverage analysis, and not FinanceBench. |
| FinSAgent, arXiv:2607.18102 (2026-07-20) | Multi-agent RAG for SEC-filing QA on FinanceBench, FinDER and SECQUE. | Abstention by prompt instruction only. No thresholds and no error target. |

## Methods the paper's statistics mirror (now cited in §2)

- **CIC**, arXiv:2607.04430 (2026-07-05). Picks the threshold whose Clopper–Pearson (or Hoeffding) upper bound on accepted-answer error is below the target. This is the paper's certified rule (§3.5). Flagged in the 2026-08-13 internal review; not cited in v1.8.
- **Kotte**, arXiv:2606.29054 (2026-06-27, v2 2026-09-07). Feasibility and impossibility results for certifying LLM outputs with conformal risk control: a minimum abstention fraction whenever base risk exceeds the target, plus a comparison of finite-sample bounds. Finding 3 (§4.4c) is a filings-QA measurement of these limits. Flagged in the internal review; not cited in v1.8.
- **UniCR**, arXiv:2509.01455 (2025-09-01). Conformal refusal under a user-specified error budget over fused uncertainty signals; general domain. Not in the 107-paper review.

## Checked and ruled out

None of these does error-targeted selective answering on filings QA. Unless marked otherwise, each was judged from its abstract.

- BudgetVerify, arXiv:2609.33052: routes answers to verification tiers to save compute; no abstention.
- Calibrated Answer Repair, arXiv:2611.05166: decides whether to repair an answer (FinRank, Fin-RATE, FinQA); no abstention.
- Token-Budgeted Escalation, arXiv:2610.07760: on all 150 FinanceBench questions, escalates from top-1 to top-5 retrieval under a token budget; no abstention.
- GBFR (ACL 2026): graph-constrained "safe abstention" in financial numerical reasoning; no error target stated.
- TempFinRAG (Symmetry, 2026): point-in-time SEC-filing QA aligned with XBRL, with a verifier that can abstain; no error target. Relevant to the companion paper.
- SecQue strategic-risk QA (MEC-J, 2026): SEC-filing QA with a refusal-control layer; no error target.
- KDAF, arXiv:2608.20661: FinanceBench (145 questions), about auditability; no abstention.
- Financial Touchstone update, arXiv:2608.08634: accuracy and hallucination rates on annual reports.
- MexRegQA, arXiv:2610.25710: evidence-sufficiency audit of regulatory QA with an abstention-permitting prompt; no thresholds.
- Financial NER selective prediction, arXiv:2608.19558: selective prediction, but for named-entity recognition, not QA.
- Evidence Sufficiency Benchmark (CMC, 2026): general RAG abstention benchmark.
- VP-CONTROL, arXiv:2609.10969: commit gates for agent actions, nominal 5% target; FinQA appears only as a side check.
- ECMR, arXiv:2610.17869: multi-agent deliberation control (MedQA, CaseHOLD, FinQA); no abstention target.
- Eliciting intrinsic hallucinations, arXiv:2608.04286: adversarial paraphrases; cites FailSafeQA.
- Reasoning's Razor (EACL): hallucination detection at low false-positive rate; not QA abstention.
- Risk-aware decision-theoretic routing (IJCNN 2026): routing between models.
- General-domain abstention or risk-control papers: arXiv:2608.17994, arXiv:2607.08456.
- Abstention on tax cases: arXiv:2609.05928.
- arXiv:2610.08322 (read in full): selective time-series forecasting, not finance.

## Limits

- 24 of the 28 candidates were judged from abstracts only.
- Semantic Scholar may not yet index the newest papers. A paper that evaluates on these benchmarks without naming them in its abstract, and is not yet indexed, could be missed. So could conference papers that are not on arXiv.
- ICAIF 2026 (14–17 Nov) falls after this check. Re-run a quick search immediately before submission.

## Changes made (rulebook v1.8.3, paper draft v1.2)

- §1: the nearest-neighbour sentence is rewritten, and contribution (1) now says "risk-targeted".
- §2: new paragraph "Closest work since mid-2026"; the selective-prediction paragraph now cites CIC, UniCR and Kotte.
- §4.4(c), §5 and §7 cross-reference these papers, and the status line is updated.
- 8 references added. No design, data, grade, analysis or reported number changed.
