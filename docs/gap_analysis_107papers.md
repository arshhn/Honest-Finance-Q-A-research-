# The Gap in RAG over Financial Filings — a 107-Paper Limitations Review

*Compiled 2026-08-01. Corpus: 107 papers (2021–2026) on RAG/LLM question answering over financial documents, gathered via arXiv, Google Scholar (driven through the user's Chrome), and the Semantic Scholar citation graph, then read for author-stated limitations and future-work sections by parallel reading agents. Extends the earlier 25-paper analysis in `rag-finance-filings-gap-analysis` (v1).*

---

## The gap, in three sentences

Across five years and every architecture generation, the single most persistent measured failure in financial-filings QA is **evidence localization inside long filings** — systems now find the right *document* almost perfectly but still cannot find the right *page, table cell, and fiscal period* — and its compounding form, cross-document evidence assembly, is close to broken. Meanwhile, the one signal that directly addresses the dominant error classes (entity/period/unit/scale confusion) already exists inside every SEC filing: **inline-XBRL anchors that bind each reported number to a standardized concept, period, unit, and entity** — yet the XBRL literature is siloed into tagging benchmarks and ground-truth generation, and no credible peer-reviewed system uses those anchors as the retrieval/verification substrate of a RAG pipeline for narrative QA (adversarially re-verified 2026-08-01 — see §3.1; the window is closing fast). **Anchor-grounded evidence localization — retrieving, aligning, and verifying against the filing's own iXBRL facts — is a precisely diagnosed, essentially unattacked gap** that simultaneously targets the four highest-frequency limitation clusters in the literature.

## 1. Method and coverage

Discovery ran in three channels: direct arXiv search; six Google Scholar queries executed in the user's Chrome session (RAG × SEC filings, finance RAG surveys, 10-K QA, earnings-call RAG, annual-report QA, XBRL × LLM); and Semantic Scholar citation-graph expansion from eight seeds (FinanceBench, SEC-QA, FinDER, HybridRAG, DocFinQA, FinQA, TAT-QA, ConvFinQA). From ~150 candidates, 108 met the relevance filter (financial documents × retrieval/QA/LLM extraction, or finance QA benchmarks, or retrieval methods evaluated on finance corpora); 107 were successfully read (one — El Amali 2025, ResearchGate — was unlocatable). Six parallel reading agents extracted author-stated limitations, future-work items, and headline weakness numbers per paper, each tagged against a fixed 17-category taxonomy. Roughly by year: 8 papers from 2021–22, 5 from 2023, 20 from 2024, 41 from 2025, 33 from 2026 — the field's publication rate roughly doubled each year since 2023.

## 2. What 107 limitations sections say

Tag frequencies across the corpus (papers whose *stated* limitations or headline failures fall in each cluster; approximate, tags assigned during extraction, up to three per paper):

| Limitation cluster | ~Papers | Emblematic numbers |
|---|---|---|
| Retrieval / evidence localization | ~40 | doc recall 0.95 but page recall 0.55 (2602.17981); chunk nDCG 0.419 vs doc 0.783 (FinAgentBench) |
| Numeric fidelity end-to-end | ~34 | 95–100% false positives on clean statements (FinVerBench); 17.3% residual numeric error (FinS-Pilot) |
| Evaluation & LLM-judge validity | ~31 | LLM judge approves 100% where experts pass 70% (FinForge); judge–human agreement 74.4% (OmniEval) |
| Multi-document / cross-entity assembly | ~22 | recall@10 9.73% cross-company (Fin-RATE); 11.89% retrieval hit rate (FinAuditing) |
| Hallucination & abstention | ~20 | most robust model fabricates in 41% of tested cases (FailSafeQA) |
| Table/layout structure loss | ~20 | 84% of TAT-QA errors from evidence extraction; multi-table F1 38.4 vs human 87.0 (MultiHiertt) |
| Cost / latency | ~18 | $3.79/query at 46.8% accuracy (Finance Agent Benchmark); ~4× LLM calls for code-gen (SEC-QA) |
| Temporal / point-in-time discipline | ~14 | period confusion = 63% of best-config errors (FinRetrieval) |
| Multimodal (charts, scans, OCR) | ~14 | mixed text+table+figure questions 40.0% vs 90.4% text-only (MultiFinRAG) |
| Query realism & conversation | ~14 | NDCG@5 drops 78.9→65.3 under query rephrasing (REAL-MM-RAG) |
| Domain transfer / generalizability | ~12 | most systems US-10-K-only by admission (FinGEAR, LEDGER, FinBen) |
| Expert-annotation bottleneck | ~12 | 71k charts cut to 1.2k for manual validation (FinChart-Bench); 300+ person-hours for 40 docs (RIRAG) |
| Structure / XBRL | ~11 | LLMs 0.0 F1 on extreme concept-linking (FinTagging); XBRL tag accuracy ~16% (RKEFino1) |
| Agentic planning limits | ~10 | agent evidence recall 23.29% best (AuditAgent) |
| Multilingual & market coverage | ~9 | benchmarks overwhelmingly US/English (+zh, minor ja/ko/th) |
| Provenance / per-number citation | ~7 | block-level citation ~61% best (FinRAGBench-V); citation accuracy not even evaluated (Finance Agent Benchmark) |
| Benchmark contamination | ~5 | filings likely in pretraining data (FinVerBench, EDINET-Bench, HiREC, FinMTEB, SEC-QA) |

Two structural observations. First, the human–model gap is remarkably stable wherever it is measured: experts score 75–93% while best systems score 40–77% (FinQA 61 vs 91; TAT-QA 58 vs 91; MultiHiertt 38 vs 87; DocMath 41 vs 76; FinDVer 76 vs 93; Fin-RATE ~43 vs 82–92; FinSearchComp 69 vs 75). Second, papers that deploy commercially tend to omit limitations sections entirely (FinSage, VeritasFi, BizBench), so the public record understates production failure modes.

## 3. THE gap: anchor-grounded evidence localization

**The diagnosis is everywhere; the treatment is nowhere.** Follow the extraction-error thread chronologically: TAT-QA (2021) attributes "about 84%" of errors to failure to extract supporting evidence; TAT-LLM (2024) still loses 48% of errors to evidence extraction; BAM embeddings (2024) report that after fixing retrieval, remaining errors are "mostly attributable" to extracting numbers from tables and deriving metrics; FinQAPT (2024) finds multi-page context extraction is the end-to-end bottleneck; FinAgentBench (2025) shows models pick the right document (nDCG 0.783) but not the right chunk (0.419); Decomposing Retrieval Failures (2026) shows document-level recall of 0.95 collapsing to 0.55 at page level; FinLongDocQA (2026) finds models cannot even locate the relevant table beyond ~129k tokens; and FinAgent-RAG (2026) shows that after program-of-thought fixes arithmetic, the residual error distribution becomes *extraction-dominated* (29.6%). Five years, five architecture generations — fixed chunking, fine-tuned retrievers, rerankers, agents, program-of-thought — and the same failure: locating the exact evidence span inside a long, boilerplate-heavy, table-dense filing.

The error taxonomy is equally consistent about *why*: near-duplicate sections across companies and years defeat semantic similarity (HiREC, 2601.11863, doc-routed 2603.26815's ticker-mismatch); models confuse fiscal periods (63% of FinRetrieval errors; HiFi-KPI's dominant date errors; FinCARDS failing cross-quarter aggregation), units and scale (FinanceComplexQA's numeric drift; FinQA's unit conversion), and entities (entity misidentification surging by 3,964 cases when Fin-RATE moves from single-document to cross-company questions). Company, period, unit, concept — exactly the four fields that **inline XBRL already pins to financial-statement figures in SEC filings, phased in 2019–2021** (large accelerated filers from mid-2019, all remaining operating companies by mid-2021).

Yet the XBRL literature and the RAG literature barely touch. The XBRL side is about *producing* tags: FinTagging finds LLMs score 0.0 F1 on extreme-scale concept linking; RKEFino1 reaches ~16% tag accuracy; XBRLTagRec improves tagging at high API cost; XBRL Agent operates on the structured facts alone (24% numeric accuracy) — and 2026 preprints (Schema-Aware XBRL tagging; XBRL-Aware LLM Agents with anti-hallucination verification) continue on the structured-statement side. The RAG side *uses XBRL only to build ground truth*: LEDGER generates 118k benchmark questions *from* XBRL anchors — and then evaluates ordinary retrievers against them (best MRR 0.475); HiFi-KPI derives labels from iXBRL. Between the two sits the unbuilt system: a RAG pipeline whose index is organized around iXBRL facts — every narrative chunk linked to the tagged concepts/periods/entities it discusses; retrieval filtered and disambiguated by anchor metadata; every extracted number verified against (and cited to) its tagged fact; refusal triggered when no anchor supports the claim. This one design attacks the top-1 cluster (localization), the temporal cluster (period discipline comes free with anchors), the numeric cluster (verification against tagged values), the provenance cluster (per-number citations are the anchors themselves), and the cross-company cluster (concept-normalized comparison across filers) — and the evaluation to prove it already exists (LEDGER, Fin-RATE EC/LT, SEC-QA, FinanceBench, FinAuditing).

Caveats stated plainly: iXBRL covers financial-statement facts, not every narrative claim (MD&A judgments, risk factors have no anchors — the system must degrade gracefully); and non-US regimes tag differently (ESEF in Europe) which is a coverage limit but also a second paper. The absence claim itself was adversarially re-verified — see §3.1.

### 3.1 Adversarial re-verification of this gap (2026-08-01)

A dedicated refutation pass ran three channels: eight Google Scholar queries (~90 results scanned) driven through the user's Chrome session; Semantic Scholar/Crossref citation pulls over XBRL Agent, FinTagging, LEDGER, HiFi-KPI, and FinAuditing plus API keyword sweeps (42 candidates surfaced); and deep classification of every borderline paper. **Outcome: the claim survives, with four qualifications a future paper must cite and differentiate against.**

**(1) A low-credibility 2023-dated journal paper claims exactly this design.** "Evidence-Grounded Trading Desk Risk Memos over SEC Filings: Retrieval-Augmented Generation with XBRL Numeric Verification" (Zhang, Meng, Zhou; *J. Advanced Computing Systems* 3(2), scipublication.com, DOI 10.69987/JACS.2023.30205) reports structured-XBRL RAG with per-number verification — at implausible perfection (100.0% numeric exactness, 100.0% citation precision, zero hallucinations, on a synthetic 1,280-filing fixture). The venue sits in an apparent citation-mill cluster: near-identical phrasing recurs across JTIE (stekom.ac.id) and Westminster-SP journal papers and two ResearchGate "XBRL-aware agent" preprints that could not be retrieved and carry improbable citation counts for 2026 uploads. The paper targets memo *generation*, not QA, uses no recognized benchmark, and predates the tooling it describes. It does not credibly occupy the gap — but it must be cited and differentiated.

**(2) The structured/audit side is being occupied fast on arXiv.** AuditFlow (2606.03031, June 2026) exposes a dynamic XBRL filing graph plus the US-GAAP taxonomy graph through typed tools for fact retrieval with deterministic audit verification (82.09% joint audit accuracy; removing the deterministic checks collapses it to 17.91%). FinReporting (2604.05966) loads tagged facts and deploys LLMs as "bounded verifiers" for cross-jurisdiction statement reporting, with only "template-based question answering for high-frequency metrics." DRBencher (2604.09251, IBM) benchmarks agents fetching EDGAR XBRL properties and doing math; FinVerBench pulls its ground truth from the EDGAR XBRL API. All of these are structured-statement tasks — none retrieves narrative filing text via anchors for open QA.

**(3) The nearest academic neighbor is paywalled and ingestion-only.** Rafanan, Largo et al., "Integrating Dense, Sparse, and Graph-Based Approaches in Financial Data Analysis for a Retrieval-Augmented Generation Framework" (IEEE conference, 2026) reads XBRL instance documents via edgar-tools as a data source feeding a hybrid dense+sparse+graph RAG for financial question answering. From all accessible text, XBRL serves ingestion/conversion; there is no evidence of anchor-level retrieval filtering, numeric verification, or per-number citation. Full text is paywalled — a paper in this gap should obtain and cite it.

**(4) Industry/OSS is building the exact idea right now, unpublished.** Red Hat's open-source *agentic-graphrag-finance* (article July 22, 2026) keeps "table rows and XBRL facts... as first-class chunk nodes with concept, period, and currency metadata," routes agentic retrieval through them, and surfaces them as ordered citations for filings QA — while stating multi-filing comparison is still being hardened. XBRL US now ships an MCP connector for retrieving as-filed facts into LLMs. Neither has an accompanying peer-reviewed paper.

**Revised verdict:** the gap stands as an *academic* contribution — no credible peer-reviewed system uses iXBRL anchors as the retrieval/verification substrate for narrative filings QA — but grey-literature implementations appeared within a month of this review, so treat the window as 6–12 months. Differentiators a new paper should own: rigorous public-benchmark evaluation (LEDGER, Fin-RATE, FinanceBench, SEC-QA), an anchor-level attribution precision/recall metric, abstention calibration on unanchored claims, and graceful handling of narrative content without anchors — none of which any neighbor above provides.

## 4. Runner-up gaps, ranked

**G2 — Cross-document evidence assembly.** The compounding version of localization. Best measured numbers are dire across independent teams: 9.73% recall@10 on cross-company comparison (Fin-RATE), 11.89% average retrieval hit rate on multi-document XBRL consistency checking (FinAuditing), 23.29% evidence recall for fraud-evidence discovery agents (AuditAgent), NDCG@5 0.749→0.302 moving from single- to four-document questions (KoBankIR), cross-document synthesis 0.44 vs 0.91 single-fact (FinDoc-RAG), 75.2% of FinMRAGBench questions needing cross-document evidence that multimodal retrievers recall at 42%. Systems that work explicitly scope it out: doc-routed retrieval (2603.26815) and FinCARDS both restrict to single filings; FinSAgent names multi-entity corpora its open problem. Nobody has shipped entity/period-normalized multi-filing retrieval — which is, again, what anchors would provide.

**G3 — Calibrated abstention and selective answering.** FailSafeQA finds the most *robust* model fabricates on 41% of perturbed/degraded inputs while the most *compliant* one over-refuses; FinTrust finds every model overconfident on unanswerable questions; FinVerBench finds 95–100% false-positive rates on clean financial statements under checklist prompting; FinanceBench documented the refusal-vs-hallucination trade-off in 2023. Only FinRAG-12B (2026, banking, 258-example eval) even attempts calibrated refusals. Conformal/selective prediction with risk guarantees on filings QA remains, per this sweep, unpublished — and it is precisely what regulated deployment needs.

**G4 — Temporal and point-in-time discipline.** Period confusion is 63% of errors in the best agentic-retrieval config (FinRetrieval); date errors dominate KPI extraction (HiFi-KPI); freshness awareness, stale evidence, and multi-source temporal reconciliation are the recurring failure modes for search agents (FinSearchComp); trend hallucination hits 8.43% (Fin-RATE); streaming/real-time indexing is named future work (2503.15191, FinS-Pilot, hierarchical reranking). Nothing handles amendments/restatements (10-K/A) or as-of-date queries; no temporally evolving benchmark exists (2506.00054's call is unanswered — FinForge names temporal data its future work).

**G5 — Evaluation infrastructure.** The judge-validity problem now has numbers: LLM validators pass 100% of questions where experts pass 70% (FinForge); judge–human agreement peaks at 74.4% even when fine-tuned (OmniEval); judge choice "sensibly influences" rankings (MCP study); BLEU/ROUGE fail to track model scale on long-form finance answers (EMS). Add contamination (5 papers state it; SEC-QA regenerates itself to dodge it) and the expert-annotation bottleneck (FinChart-Bench cut 71k→1.2k; FinMRAGBench size-capped by expert validation; RIRAG spent 300+ person-hours on 40 documents; FinTextQA constrained by copyright). A verified, numeric-aware, contamination-resistant evaluation stack for filings QA would be cited by every paper in this table. The dedicated finance-RAG survey also still does not exist (closest: a 2024 Kronika journal survey and two 2026 SSRN/Springer reviews of adjacent scope).

## 5. Where it is crowded — do not enter without a sharp angle

Hybrid dense+sparse retrieval with reranking on FinanceBench/FinDER: at least eight papers in 2024–26 (2603.16877, 2503.15191, 2404.07221, SILCON, hierarchical reranking, FinCARDS, FinQAPT, NAACL pipelines). Multi-agent/agentic QA wrappers: ten-plus (FinSAgent, FinAgent-RAG, Multi-HyDE, FinMAN, MimirRAG, FinDebate, FinRobot line, Aethel, AuditAgent, FinLongDocAgent). Chunking/parsing studies: four (2402.05131, 2604.12047, MultiFinRAG's pipeline, T2-RAGBench ablations). KG-hybrid retrieval: six (HybridRAG, FinReflectKG line, Agentic GraphRAG, Structure-First, Aethel, GRI-style). New entrants need a diagnosed mechanism (as FinSAgent's "prior-corpus misalignment" or Fin-STAR's "structure-as-semantics"), not an architecture remix. Benchmarks are *not* saturated in specific niches: point-in-time/restatement-aware, abstention-scored, and anchor-grounded evaluation all lack a benchmark.

## 6. What a paper in the primary gap looks like

A concrete, executable slate: (1) **System** — build the iXBRL-anchored index over EDGAR filings (anchors are free; EDGAR is free): chunk-to-fact linking at parse time, anchor-metadata-filtered retrieval, arithmetic verification against tagged facts, anchor-derived per-number citations, abstention when unanchored. (2) **Evaluation** — LEDGER (retrieval + KPI tiers), Fin-RATE EC/LT (cross-company/longitudinal), FinanceBench + SEC-QA (compatibility), FinAuditing (consistency checking); report attribution precision/recall, not just answer accuracy. (3) **Expected contributions** — first quantification of how much of the localization gap (0.95→0.55) anchor grounding closes; a per-number attribution metric; an abstention-calibration curve. Secondary slates: the point-in-time benchmark with 10-K/A restatement pairs and as-of queries, regenerable from EDGAR (attacks G4+G5, contamination-resistant by construction); or the selective-prediction study on FailSafeQA+FinanceBench with conformal risk control (G3, cheap to run, high citation surface).

## 7. Full inventory (107 papers)

Tags: retr = retrieval/localization, multi = multi-document, temp = temporal, num = numeric, table = table/layout, mm = multimodal, prov = provenance/citation, hall = hallucination/abstention, eval = evaluation/judge, contam = contamination, cost = cost/latency, transfer = generalizability, lang = multilingual/coverage, query = query realism/conversational, struct = structure/XBRL, agents = agentic planning, data = annotation bottleneck.

| # | Paper | ID | Yr | Core stated limitation / headline failure | Tags |
|---|---|---|---|---|---|
| 1 | FinanceBench | 2311.11944 | 2023 | 81% fail/refuse with retrieval; single-turn; no cross-company Qs | retr, hall, query |
| 2 | DocFinQA | 2401.06915 | 2024 | retrieval hit rate caps accuracy on 100K+-token filings | retr, num |
| 3 | Financial Report Chunking | 2402.05131 | 2024 | judge fails on elaborate answers; inter-element relations open | table, eval |
| 4 | SEC-QA | 2406.14394 | 2024 | vanilla RAG ~30% multi-doc; code-gen fix costs ~4× calls | multi, num, contam |
| 5 | HybridRAG | 2408.04948 | 2024 | KG+vector union lowers precision; numeric analysis future work | retr, num, eval |
| 6 | OmniEval | 2412.13018 | 2024 | multi-hop and conversational weakest; judge agreement 74.4% | multi, query, eval |
| 7 | FinTMMBench | 2503.05185 | 2025 | best system F1 23.71; retrieval = 46.5% of errors | temp, mm, retr |
| 8 | FinSage | 2504.14493 | 2025 | production system; no limitations section published | mm, transfer |
| 9 | RAG evaluation survey | 2504.14891 | 2025 | domain-specific RAG evaluation excluded as unresolved | eval |
| 10 | FinDER | 2504.15800 | 2025 | real analyst queries: best retrieval recall 25.95% | query, retr |
| 11 | FinRAGBench-V | 2505.17471 | 2025 | block-level visual citation unsolved (best ~61%) | mm, prov |
| 12 | HiREC / LOFin | 2505.20368 | 2025 | contamination concern; multi-document reasoning weak | multi, contam, retr |
| 13 | RAG robustness survey | 2506.00054 | 2025 | temporal drift; poisoning defenses only partial | temp, eval |
| 14 | Multi-HyDE | 2509.16369 | 2025 | hallucinations persist; requires human oversight | hall, eval, cost |
| 15 | FinReflectKG-MultiHop | 2510.02906 | 2025 | inter-year hops hardest; LLM-judge bias | temp, multi, eval |
| 16 | Multimodal doc-RAG survey | 2510.15253 | 2025 | element-level table/chart retrieval open; OCR fragility | mm, table, cost |
| 17 | Rethinking Retrieval (PwC) | 2511.18177 | 2025 | ToC-navigation bottleneck; domain rerankers unexplored | retr, struct, cost |
| 18 | Metadata for RAG | 2601.11863 | 2026 | 10-K-only stress corpus; frozen encoders; retrieval-only eval | retr, transfer, eval |
| 19 | Fin-RATE | 2602.07294 | 2026 | cross-company recall@10 9.73%; missing evidence 75.44% | multi, temp, hall |
| 20 | Reranking analysis | 2603.16877 | 2026 | recall ceiling; multi-hop weak; judge verbosity bias | multi, eval, cost |
| 21 | FinAgent-RAG | 2605.05409 | 2026 | post-PoT residual errors extraction-dominated (29.6%) | retr, num |
| 22 | FinSAgent | 2607.18102 | 2026 | multi-entity cross-document reasoning left open | multi, cost, transfer |
| 23 | FinanceComplexQA | 2607.19238 | 2026 | numeric drift; layout confusion; over-synthesis | num, table, hall |
| 24 | Agentic RAG survey | 2501.09136 | 2025 | process-aware eval, governance, convergence all open | agents, eval, prov |
| 25 | FinQA | 2109.00122 | 2021 | regular-layout tables only; ~30-pt gap to experts | num, table, retr |
| 26 | ConvFinQA | 2210.03849 | 2022 | long reasoning dependencies hardest; ~20-pt expert gap | num, query, cost |
| 27 | TAT-QA | 2105.07624 | 2021 | "about 84%" of errors from evidence extraction | num, retr, table |
| 28 | TAT-DQA | 2207.11871 | 2022 | long visually-rich documents "a big challenge" | mm, table, num |
| 29 | MultiHiertt | 2206.01347 | 2022 | multi-table hierarchy fails; F1 38.4 vs human 87.0 | table, num, retr |
| 30 | PACIFIC | 2210.08817 | 2022 | basic calculations only; charts/images excluded | query, num, mm |
| 31 | DocMath-Eval | 2311.09805 | 2023 | answer extraction approximate; ~36-pt expert gap on hard split | num, eval, retr |
| 32 | BizBench | 2311.06602 | 2023 | most models "miss over 3/4 of the problems" | num, transfer |
| 33 | FinBen | 2402.12659 | 2024 | US-English only; ≤70B open models; forecasting near random | lang, temp, cost |
| 34 | TAT-LLM | 2401.13223 | 2024 | 48% of errors from evidence extraction; 4K context cap | num, retr, cost |
| 35 | FinanceReasoning | 2506.05828 | 2025 | tables as text only; no ambiguity/clarification handling | num, mm, query |
| 36 | Math-reasoning eval | 2402.11194 | 2024 | accuracy degrades with reasoning steps; extraction 35–52% of errors | num, table, cost |
| 37 | FinLongDocQA | 2604.03664 | 2026 | cannot locate relevant tables beyond ~129k tokens | retr, num, agents |
| 38 | ECTSum | 2210.12467 | 2022 | "factual consistency scores... generally low" across methods | hall, data |
| 39 | Improving Retrieval for RAG | 2404.07221 | 2024 | zero-shot retrieval fixes "not nearly enough" | retr, hall |
| 40 | Optimizing retrieval strategies | 2503.15191 | 2025 | streaming data and multilingual open; MultiHiertt NDCG 0.247 | temp, lang, table |
| 41 | FinQAPT | 2410.13959 | 2024 | end-to-end drops sharply; multi-page extraction bottleneck | retr, num, table |
| 42 | FinGEAR | 2509.12042 | 2025 | US 10-K only; parsing-noise sensitive; terminology drift | transfer, struct, num |
| 43 | Fin-STAR | ACL-F 2026 | 2026 | routing "performance ceilings"; hallucination remains | struct, retr, hall |
| 44 | Doc-routed hybrid retrieval | 2603.26815 | 2026 | single-company only; ticker-mismatch sensitivity | multi, retr |
| 45 | Hierarchical reranking | 2607.27523 | 2026 | reranking overhead; 64k cap limits multi-document use | cost, lang, temp |
| 46 | FinCARDS | 2601.06992 | 2026 | single filing scope; cross-quarter aggregation fails | cost, multi, temp |
| 47 | MimirRAG | 2605.25030 | 2026 | OCR/table extraction errors; 150-question eval | table, eval, transfer |
| 48 | Bayesian RAG | Frontiers AI | 2026 | 24-question eval; 8.3% high-confidence false positives | hall, eval, cost |
| 49 | Structure First, Reason Next | 2601.07754 | 2026 | single benchmark (FinQA), single 8B model | num, transfer |
| 50 | Aethel | 2607.24826 | 2026 | graph gain pool-dependent; BM25 survives open-corpus; 1 annotator | multi, retr, data |
| 51 | MCP bypass (LSEG APIs) | 2603.20316 | 2026 | "breaks down" on qualitative/document-specific questions | eval, agents, query |
| 52 | RIRAG / ObliQA | 2409.05677 | 2024 | semi-synthetic questions; expert shortage; 300+ h for 40 docs | data, transfer, eval |
| 53 | MultiFinRAG | 2506.20821 | 2025 | PDF/OCR brittle; mixed-modality questions 40.0% | mm, table, multi |
| 54 | Metadata-driven RAG | 2510.24402 | 2025 | judge-only eval; 12.2% hallucination in best config | eval, retr, hall |
| 55 | Enhancing LLM performance | 2402.01722 | 2024 | "simple RAG pipelines often fail" complex documents | retr, transfer |
| 56 | RAG eval on bank reports | 10.3390/app14209318 | 2024 | similar-number disambiguation errors; PDF layout trouble | table, num, eval |
| 57 | Optimizing pipelines (NAACL-I) | 2024.naacl-industry.23 | 2024 | single-passage answer assumption unrealistic | retr, multi |
| 58 | Quant-finance RAG (INFUS) | Springer | 2024 | positioned as preliminary; abstract-only access | cost, eval |
| 59 | FinDoc-RAG (FinNLP) | 2025.finnlp-2.9 | 2025 | cross-document synthesis 0.44 vs 0.91 extraction | multi, eval, query |
| 60 | FinMAN (David vs Goliath) | 2025.findings-emnlp.225 | 2025 | MCTS verification most time-consuming; FQA-only | agents, num, cost |
| 61 | PDF parsing/chunking eval | 2604.12047 | 2026 | best end-to-end 54%; judge under/over-penalizes | table, eval, transfer |
| 62 | Decomposing retrieval failures | 2602.17981 | 2026 | document recall 0.95 vs page recall 0.55 | retr |
| 63 | Scalable 10-K framework | 2409.17581 | 2024 | sections "not as meaningfully captured"; rating bias | struct, eval |
| 64 | FinRAG-12B | 2605.05482 | 2026 | 258-example eval; retail-banking skew | transfer, hall, prov |
| 65 | Hybrid regulatory retrieval | 2502.16767 | 2025 | low answer-passage entailment (RePASs 0.57) | hall, retr, transfer |
| 66 | SECQUE | 2504.04596 | 2025 | judge bias; multiple valid calculation paths | eval, num, transfer |
| 67 | T2-RAGBench | 2506.12071 | 2025 | ~30-pt gap between RAG and oracle context | retr, table, query |
| 68 | SMARTFinRAG | 2504.18024 | 2025 | best faithfulness 0.60; OCR unimplemented | eval, hall, mm |
| 69 | FinTextQA | 2405.09980 | 2024 | small dataset; copyright prevents sharing | data, retr |
| 70 | LEDGER | 2606.13100 | 2026 | OCR errors in dense tables; best retrieval MRR 0.475; US-only | table, retr, struct |
| 71 | FinAgentBench | 2508.14052 | 2025 | chunk-level nDCG 0.419 vs document-level 0.783 | agents, retr |
| 72 | FinRetrieval | 2603.04403 | 2026 | period confusion = 63% of errors in best config | temp, agents, retr |
| 73 | FinS-Pilot | 2506.02037 | 2025 | 17.3% residual numerical error despite retrieval | temp, num, hall |
| 74 | VeritasFi | 2510.10828 | 2025 | no limitations section; per-deployment expert annotation | mm, data, cost |
| 75 | FinMRAGBench | 2026.findings-acl.187 | 2026 | multimodal recall@10 42.46%; 75.2% questions cross-document | mm, multi, retr |
| 76 | FinForge | 2601.06747 | 2026 | LM judge approves 100% where experts pass 70% | eval, query, temp |
| 77 | KoBankIR query-gen | 2511.05000 | 2025 | NDCG@5 0.749 single-doc → 0.302 on 4-doc | multi, lang, query |
| 78 | EMS evaluation paradigm | 2503.16575 | 2025 | qualitative-only; LLM-generated references | eval, data, num |
| 79 | FinSearchComp | 2509.13160 | 2025 | freshness, multi-source reconciliation, temporal gaps | temp, agents, multi |
| 80 | FinDVer | 2411.05764 | 2024 | GPT-4o 76.2% vs experts 93.3%; tabular encoding open | num, table, eval |
| 81 | FinGround | 2604.23588 | 2026 | regeneration compounds errors (4.1%); numeric claims weakest | hall, prov, num |
| 82 | FailSafeQA | 2502.06329 | 2025 | most robust model fabricates in 41% of cases | hall, query, multi |
| 83 | FinTrust | 2510.15232 | 2025 | all models overconfident on unanswerable questions | hall |
| 84 | FinLFQA | 2510.06426 | 2025 | two-company scope; grounding and numeric attribution weak | prov, num, hall |
| 85 | FRED | 2507.20930 | 2025 | synthetic-data-only evaluation; mechanisms opaque | hall, data |
| 86 | LLM deficiency in finance | 2311.15548 | 2023 | Llama2-7B 0% on price queries; fixes task-specific | hall, temp, retr |
| 87 | Reducing hallucination (extraction) | 2310.10760 | 2023 | retrieval pulls "unrelated entities" across documents | retr, multi, hall |
| 88 | FinTruthQA | 2406.12009 | 2024 | Chinese-market specificity; annotation subjectivity | data, lang, transfer |
| 89 | FinMTEB | 2502.10990 | 2025 | BoW beats dense on financial STS; contamination risk | contam, transfer, lang |
| 90 | BAM embeddings | 2411.07142 | 2024 | residual errors "mostly attributable" to table numbers/derived metrics; data proprietary | retr, table, query |
| 91 | Embedding distillation for filings | 2512.08088 | 2025 | sampling misses aspects; second iteration mixed | retr, eval, agents |
| 92 | HiFi-KPI | 2502.15411 | 2025 | iXBRL label noise; date errors dominate | struct, data, num |
| 93 | FinVerBench | 2605.29586 | 2026 | 95–100% false positives on clean statements | num, contam, eval |
| 94 | XBRL Agent | ICAIF '24 | 2024 | 24% numeric accuracy; cross-jurisdiction rules unresolved | struct, num, agents |
| 95 | FinTagging | 2505.20650 | 2025 | LLMs 0.0 F1 on extreme concept linking | struct, num, table |
| 96 | XBRLTagRec | 2603.25263 | 2026 | re-ranking API costs; rounds saturate ~8 | struct, cost, retr |
| 97 | RKEFino1 | 2506.05700 | 2025 | XBRL tag accuracy ~16%; numerical NER 26.6 F1 | struct, num, data |
| 98 | FinAuditing | 2510.08886 | 2025 | 11.89% retrieval hit rate; 60–90% accuracy drops multi-doc | multi, struct, num |
| 99 | AuditAgent | 2510.00156 | 2025 | best evidence-level recall 23.29% | multi, agents, retr |
| 100 | Finance Agent Benchmark | 2508.00828 | 2025 | no model >50%; $3.79/query; citations unevaluated | agents, prov, cost |
| 101 | FinReflectKG | 2508.17906 | 2025 | cross-document coreference partial; judge bias | eval, multi, table |
| 102 | Agentic GraphRAG (SHAB) | 2605.18770 | 2026 | true recall unauditable at 7M docs; Swiss specificity | eval, retr, transfer |
| 103 | FinDebate | 2509.17395 | 2025 | 15-report eval; refines existing recommendations only | agents, eval |
| 104 | FinChart-Bench | 2507.14823 | 2025 | 71k charts cut to 1.2k (manual validation); spatial inference weak | mm, eval, data |
| 105 | REAL-MM-RAG | 2502.12342 | 2025 | NDCG drops under rephrasing; single-page retrieval only | retr, query, table |
| 106 | EDINET-Bench | 2506.08762 | 2025 | contamination risk; label noise; near-logistic-regression results | contam, lang, data |
| 107 | AlphaFin | 2403.12582 | 2024 | "still great room for development"; Chinese-market scope | transfer, lang |

## 8. Caveats

Tag counts are approximate (assigned during extraction, ≤3 per paper); several papers were abstract-only (INFUS 2024, FinLongDocQA at read time); one candidate was unlocatable (El Amali 2025); non-arXiv venue items (Fin-STAR, FinMRAGBench, FinDoc-RAG, FinMAN, XBRL Agent) were read from ACL Anthology/ACM/NSF copies. Quotes are under 15 words each; all other limitation text is close paraphrase. Numbers cited in sections 2–4 were re-verified against sources for the headline claims (see verification note in the conversation); re-check any figure against the PDF before citing it in a manuscript. The primary-gap claim was adversarially re-verified on 2026-08-01 (§3.1) and survives with the qualifications listed there; nearest neighbors: LEDGER (XBRL as benchmark ground truth), HiFi-KPI (labels), XBRL Agent/AuditFlow/FinReporting (structured statements), Rafanan et al. (XBRL as ingestion into hybrid RAG, paywalled), one low-credibility 2023 journal claim, and Red Hat's unpublished OSS prototype.
