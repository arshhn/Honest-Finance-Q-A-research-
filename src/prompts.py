"""Pinned prompts for Paper 1. DO NOT EDIT after runs begin (design.md changelog v1.2).

The ask protocol follows docs/design.md verbatim; the closed-book and
missing-document variants are pinned here per changelog v1.2.
"""

ORACLE_TEMPLATE = """You are answering a question about a company's SEC filing. Use ONLY the provided document text.
Document: {evidence}
Question: {question}
Rules: If the document does not contain enough information, reply exactly "CANNOT ANSWER".
Reply in this format —
ANSWER: <your answer, with units>
CONFIDENCE: <integer 0–100, how likely your answer is correct>"""

CLOSEDBOOK_TEMPLATE = """You are answering a question about a company's SEC filing. No document is provided; answer from your own knowledge.
Question: {question}
Rules: If you are not confident you know the answer, reply exactly "CANNOT ANSWER".
Reply in this format —
ANSWER: <your answer, with units>
CONFIDENCE: <integer 0–100, how likely your answer is correct>"""

# FailSafeQA missing-context condition: identical protocol, explicit empty document.
MISSING_DOC_TEXT = "[NO DOCUMENT PROVIDED]"

PARAPHRASE_PROMPT = """Rewrite the following question so it asks for exactly the same information using clearly different wording. Preserve every entity name, fiscal period, unit, and the required answer format. Do not answer the question. Reply with ONLY the rewritten question, nothing else.

Question: {question}"""

GRADER_PROMPT = """You are grading one exam answer about a company's SEC filing. Compare the candidate answer to the gold answer.

Question: {question}

Gold answer: {gold}

Candidate answer: {candidate}

Grade CORRECT if the candidate conveys the same substantive answer as the gold (numeric values must match within 1% AND be in the same units/scale; extra correct detail is fine).
Grade INCORRECT if the candidate gives a different, wrong, or contradictory answer, or answers a different question.
Grade REFUSED if the candidate declines to answer, says it cannot answer, or gives no substantive answer.

Reply with exactly one word: CORRECT or INCORRECT or REFUSED."""

AGREEMENT_PROMPT = """Two people answered the same question about a company's SEC filing. Decide whether their answers convey the same substantive answer (numbers matching within 1%, same units/scale).

Question: {question}

Answer A: {a}

Answer B: {b}

Reply with exactly one word: YES if they convey the same answer, NO otherwise."""
