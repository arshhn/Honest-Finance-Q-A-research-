# Is There a Research Gap in RAG over Financial Filings?

**Short answer: yes — several, and they are unusually well quantified.** The space is crowded at the level of "build a RAG pipeline for 10-K question answering," but as of August 2026 the literature itself documents large, measured failure modes that no published system closes. The strongest openings are cross-filing comparison, temporal/point-in-time grounding, per-number provenance, numeric-faithful evaluation, and abstention calibration.

*Compiled 2026-08-01 from an arXiv sweep (~25 papers read for stated limitations and future-work sections). Google Scholar pass pending — the Chrome extension was not connected during this session.*

---

## 1. State of the field in one page

The benchmark lineage tells the story. FinanceBench (arXiv 2311.11944, Nov 2023) showed that GPT-4-Turbo with a retrieval system "incorrectly answered or refused to answer 81% of questions" over SEC filings. DocFinQA (2401.06915, ACL 2024) extended QA to full 10-Ks (~123K words average) and found retrieval hit rates as low as 0.35 top-1, capping end accuracy near 43%. SEC-QA (2406.14394, 2024) showed vanilla RAG scores ~30% on multi-document questions. FinDER (2504.15800, ICLR '25 workshop), built from real hedge-fund analyst queries, measured best-case retrieval recall of just 25.95% and best generation correctness ~32%. By 2026 the benchmarks became harsher and more diagnostic: Fin-RATE (2602.07294, KDD '26) reports the best frontier model at ~43% on its cross-company comparison task versus human experts at 82–92% across tasks, with cross-company retrieval recall@10 of **9.73%** and missing evidence in 75% of cases; FinanceComplexQA (2607.19238, July 2026) finds even the best agentic system (Claude Code + Sonnet) at ~69–76%, with numerical comparison and layout-heavy documents the weakest categories.

On the systems side, the progression ran: structure-aware chunking (Unstructured, 2402.05131) → hybrid KG+vector retrieval (HybridRAG, BlackRock/NVIDIA, 2408.04948) → multi-aspect production RAG (FinSage, 2504.14493, CIKM '25) → hierarchical retrieval with evidence curation (HiREC, 2505.20368, ACL '25 Findings) → agentic and multi-agent systems in 2025–26 (Multi-HyDE 2509.16369, FinAgent-RAG 2605.05409, FinSAgent 2607.18102) → a PwC head-to-head of vector-agentic versus non-vector hierarchical navigation (2511.18177). Each generation improves on the previous benchmark and then documents, in its own limitations section, the same residual failures.

Two meta-observations matter for positioning. First, no dedicated peer-reviewed survey of RAG for finance appeared on arXiv in 2024–2026 (the general RAG-evaluation survey 2504.14891 explicitly scopes out domain-specific RAG evaluation) — a survey is itself a publishable contribution. Second, the field's own evaluation instruments are contested: LLM-as-judge misgrades numeric answers, gold labels are "valid but still contestable" (FinanceBench), and public benchmarks face contamination pressure (HiREC notes models "have already been exposed to these datasets").

## 2. The gaps, ranked by evidence strength

**G1 — Cross-document, cross-company, and cross-year retrieval is close to broken.** This is the single best-documented gap. Fin-RATE measured recall@10 of 9.73% on enterprise-comparison questions with "Missing Evidence" at 75.44%, plus thousands of entity-misidentification cases; SEC-QA showed pipelines "systematically fail" on multi-document questions (~30% for vanilla RAG); FinReflectKG-MultiHop found inter-year questions the hardest hop type and includes only 9.7% cross-company questions because they are hard to build; FinanceBench excluded cross-company questions entirely as future work. The mechanism is understood — near-duplicate boilerplate across companies and years defeats semantic similarity, and only coarse metadata (company, fiscal year) reliably disambiguates (2601.11863) — but no published system fixes it. FinSAgent (July 2026) names "multi-entity corpora requiring sequential cross-document reasoning" as its open problem. A system with entity- and period-aware indexing evaluated on Fin-RATE EC/LT and SEC-QA multi-doc splits would attack the field's biggest measured hole.

**G2 — Temporal and point-in-time grounding.** Models misassign fiscal periods, hallucinate trends (8.43% of Fin-RATE longitudinal answers), and stumble on terminology that evolves across reporting years (FinReflectKG-MultiHop). FinTMMBench (2503.05185), the only temporal-aware multimodal finance benchmark, reports its own best system at F1 23.71 — the authors call this evidence of "the need for more advanced RAG methods." The robustness survey (2506.00054) calls for "temporally evolving benchmarks" that do not exist yet. Nothing in the literature handles amended/restated filings (10-K/A), as-of-date correctness, or proposed-versus-enacted rule distinctions that practitioners flag as first-order relevance signals.

**G3 — Structure, tables, footnotes, and XBRL.** Flattening filings to text "strips away structural and semantic information": multi-level table headers detach from values (FinanceComplexQA's "layout confusion"), footnote anchors break, and element-level retrieval of tables/charts is an open problem per the multimodal-RAG survey (2510.15253). Structure-aware approaches win when tried — SEC-QA's code-generation over structured pages gains ~50 points over RAG; KG-linked evidence gives ~24% correctness gain with ~84.5% fewer tokens (FinReflectKG-MultiHop) — yet the PwC study found pure hierarchical/ToC navigation has its own "retrieval bottleneck at the table-of-contents level." Notably, **XBRL — the machine-readable tagging that already exists in every SEC filing — is essentially absent from the RAG literature** as a retrieval-grounding signal; the sweep found no paper anchoring narrative-QA retrieval to XBRL facts. That is a concrete, low-hanging research direction.

**G4 — Numeric fidelity survives retrieval fixes.** Even when retrieval succeeds, models drift on period, unit, and sign (FinanceComplexQA); compound/derived metrics score 33.3% versus 89.5% for single-value extraction (SEC-QA). And after program-of-thought removes arithmetic errors, the bottleneck moves rather than disappears: FinAgent-RAG (2605.05409) reports the residual error distribution shifts from arithmetic-dominated (38.8%) to **data-extraction-dominated (29.6%)** — locating the right number is now the dominant failure. FinanceBench's oracle setting (gold evidence provided) still yields ~15% wrong answers, so grounding alone does not close the loop.

**G5 — Provenance, citation, and auditability.** FinRAGBench-V shows page-level citation is largely workable for top models (~89–93% recall) but block-level visual citation "remains difficult" (best ~61%, open-source models far lower); the agentic-RAG survey calls for "process-aware evaluation" and "transparent decision-tracing"; practitioners insist every number needs CIK/accession/section provenance to be usable in regulated workflows. No benchmark scores per-number attribution precision/recall for filings QA. For an auditable-by-construction system — answer = value + exact table-cell citation — both the method and the evaluation instrument are open.

**G6 — Evaluation methodology for finance RAG.** The RAG-evaluation survey (2504.14891) excludes domain-specific evaluation as architecturally unresolved; multiple papers report LLM judges misgrading numeric or verbose answers (Multi-HyDE: "LLM-based evaluation often incorrectly evaluates responses"); OmniEval needed a fine-tuned evaluator and still reached only 74.4% human agreement; SEC-QA regenerates itself from fresh filings specifically to dodge contamination. A verified, numeric-faithful evaluation protocol (or judge) for financial QA would be widely cited infrastructure.

**G7 — Realistic queries, conversation, and intent.** FinDER showed terse, jargon-heavy real analyst queries cut retrieval precision ~8 points versus clean benchmark questions; FinanceBench is single-turn by design though "analysts ask follow-ups"; OmniEval finds conversational QA among the weakest tasks. Financial user-intent modeling (which "exposure"? which "margin"?) is explicitly called an open problem in practitioner writing.

**G8 — The hallucination–refusal tradeoff is uncalibrated.** Under weak retrieval GPT-4-Turbo refuses 68–88% of the time while Llama-2 fabricates (70% incorrect); Fin-RATE logs hallucination surges precisely on comparison questions; agents "over-synthesize" unsupported claims (FinanceComplexQA). Selective prediction / calibrated abstention with risk guarantees has, per this sweep, not been studied for filings RAG — despite being exactly what enterprise deployment needs.

**G9 — Cost, latency, and small open models.** The things that work are expensive: long-context prompting is "impractical" at enterprise latency (FinanceBench), code-generation pipelines need ~4x LLM calls (SEC-QA), rerankers add latency and API cost (2603.16877), and results swing by closed-source backbone (FinSAgent). Multi-HyDE proposes fine-tuned small open models as agents but does not evaluate them. An efficient, open-weights filings-RAG stack with a measured accuracy/cost frontier is open.

**G10 — Coverage beyond S&P-500 10-Ks in English.** Most benchmarks draw from large-cap US annual reports. 6-Ks, proxy statements (DEF 14A), prospectuses, 8-K event filings, scanned/OCR documents ("poor performance on real-world PDFs with OCR errors or dense numerical content," 2510.15253), non-US regimes, and languages beyond English/Chinese are thinly covered. Fin-RATE and FinanceComplexQA began widening filing types in 2026, but small-cap, municipal, and international disclosure remain open corpora.

## 3. Where it is crowded — avoid these as thesis topics

Single-document 10-K QA with hybrid dense+sparse retrieval plus a reranker is saturated (FinSage, HiREC, 2603.16877, and many workshop papers); another FinanceBench leaderboard entry adds little. Generic "agentic RAG wrapper" papers without a diagnosed failure mode are also proliferating in 2026 (FinSAgent, FinAgent-RAG, Multi-HyDE already occupy this lane). KG+vector hybrids exist (HybridRAG) though their context-precision problem is unsolved. If you work in these lanes, you need a sharply diagnosed mechanism (as FinSAgent did with "prior-corpus misalignment") rather than an architecture remix.

## 4. Concrete directions a new paper could take

The highest-leverage combinations of gap × feasibility, given that filings are public and EDGAR is free: (1) **XBRL-anchored retrieval** — use the filing's own tagged facts as a structured index that grounds and verifies narrative retrieval, evaluated on Fin-RATE EC/LT and SEC-QA (attacks G1+G3+G4). (2) **A point-in-time benchmark** with amendments/restatements and as-of queries, continuously regenerable from EDGAR to resist contamination (G2+G6). (3) **Per-number provenance QA** — systems must return value plus exact source cell/section; introduce attribution precision/recall metrics (G5). (4) **Calibrated abstention for filings RAG** — selective answering with conformal-style risk control on FinanceBench/Fin-RATE (G8). (5) **A numeric-faithful judge** — a verified evaluator for financial answers, validated against expert grading (G6). (6) **The missing survey** of RAG for financial documents (2023–2026).

## 5. Paper inventory

| Paper | arXiv | Date | Type | Key takeaway for gaps |
|---|---|---|---|---|
| FinanceBench | 2311.11944 | 2023-11 | Benchmark | 81% fail/refuse with retrieval; single-turn; no cross-company Qs |
| DocFinQA | 2401.06915 | 2024-01 | Benchmark | Full-10-K contexts; retrieval hit rate caps accuracy |
| Financial Report Chunking | 2402.05131 | 2024-02 | System | Element-based chunking helps; inter-element relations open |
| SEC-QA | 2406.14394 | 2024-06 | Benchmark | Multi-doc RAG ~30%; code-gen +50 pts at ~4x cost |
| HybridRAG (BlackRock/NVIDIA) | 2408.04948 | 2024-08 | System | KG+vector union hurts precision; numeric analysis future work |
| OmniEval | 2412.13018 | 2024-12 | Benchmark | Multi-hop & conversational weakest; judge agreement 74.4% |
| FinDER / ICAIF FinanceRAG | 2504.15800 | 2025-04 | Benchmark | Real analyst queries; retrieval recall 25.95% |
| FinSage | 2504.14493 | 2025-04 | System | Production system; no limitations section published |
| RAG eval survey | 2504.14891 | 2025-04 | Survey | Domain-specific RAG evaluation explicitly out of scope |
| FinTMMBench | 2503.05185 | 2025-03 | Benchmark | Temporal multimodal; best F1 23.71; retrieval = 46.5% of errors |
| HiREC / LOFin | 2505.20368 | 2025-05 | System+bench | Hierarchical retrieval; contamination concern; multi-doc weak |
| FinRAGBench-V | 2505.17471 | 2025-05 | Benchmark | Page-level citation ~90%; block-level citation unsolved |
| General RAG survey (robustness focus) | 2506.00054 | 2025-05 | Survey | Temporal drift, poisoning defenses, provenance filtering open |
| Multi-HyDE | 2509.16369 | 2025-09 | System | Hallucinations persist; needs human oversight; small-LM agents untested |
| FinReflectKG-MultiHop | 2510.02906 | 2025-10 | Benchmark | Inter-year hardest; KG evidence +24% acc, −84.5% tokens |
| Multimodal doc-RAG survey | 2510.15253 | 2025-10 | Survey | Element-level table/chart retrieval, OCR robustness open |
| Rethinking Retrieval (PwC) | 2511.18177 | 2025-11 | Study | Vector-agentic beats ToC-hierarchy; domain rerankers open |
| Metadata for RAG | 2601.11863 | 2026-01 | Study | Company/year metadata is the disambiguator; learned fusion open |
| Fin-RATE | 2602.07294 | 2026-02 | Benchmark | Humans 82–92 vs LLMs ~43; cross-company recall@10 9.73% |
| Reranking analysis | 2603.16877 | 2026-03 | System | +15.5 pp from reranking; recall ceiling; multi-hop weak |
| FinAgent-RAG | 2605.05409 | 2026-05 | System | PoT fixes math; extraction becomes dominant error (29.6%) |
| FinSAgent | 2607.18102 | 2026-07 | System | Multi-agent; multi-entity cross-doc reasoning left open |
| FinanceComplexQA | 2607.19238 | 2026-07 | Benchmark | Best agents 69–76%; numeric drift, layout confusion, over-synthesis |

## 6. Method and caveats

Method: arXiv discovered via targeted web search (the export.arxiv.org API is robots-blocked for fetching), then three parallel reading agents extracted abstracts, headline numbers, and limitations/future-work sections from `arxiv.org/abs` and `arxiv.org/html` pages, plus two practitioner sources (DealCharts, FinTech Studios) for deployment pain points. Caveats: quotes were kept under 15 words and close-paraphrased elsewhere, but figures should be re-verified against the PDFs before citing in a paper; the Google Scholar pass (citation counts, non-arXiv venues such as journal finance-NLP work) has not run yet because the Chrome extension was offline; "no XBRL-grounded RAG paper found" and "no dedicated finance-RAG survey found" are absence-of-evidence claims from this sweep, not proofs of absence.
