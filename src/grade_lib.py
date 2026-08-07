"""Answer parsing + numeric grading. Pure Python, no API. Pinned per design.md v1.2."""
import re

REFUSAL_RE = re.compile(r"cannot\s+answer", re.IGNORECASE)

_NUM_RE = re.compile(r"[-+]?\(?\$?\s*\d[\d,]*\.?\d*\)?%?")
_SCALE_WORDS = [
    (re.compile(r"billion", re.I), 1e9),
    (re.compile(r"\bbn\b", re.I), 1e9),
    (re.compile(r"million", re.I), 1e6),
    (re.compile(r"\bmn\b|\bmm\b", re.I), 1e6),
    (re.compile(r"thousand", re.I), 1e3),
]


def parse_response(text: str):
    """Extract (answer, confidence, refused, parse_ok) from a model reply."""
    if not text:
        return "", None, False, False
    ans_m = re.search(r"ANSWER:\s*(.+?)(?:\n\s*CONFIDENCE:|\Z)", text, re.S | re.I)
    conf_m = re.search(r"CONFIDENCE:\s*(\d{1,3})", text, re.I)
    answer = ans_m.group(1).strip() if ans_m else text.strip()
    confidence = min(100, int(conf_m.group(1))) if conf_m else None
    refused = bool(REFUSAL_RE.search(answer)) or bool(
        REFUSAL_RE.search(text) and not ans_m)
    parse_ok = bool(ans_m)
    return answer, confidence, refused, parse_ok


def extract_number(s: str):
    """First number in s, scale-word adjusted. Returns float or None."""
    if not s:
        return None
    m = _NUM_RE.search(s)
    if not m:
        return None
    raw = m.group(0)
    neg = raw.strip().startswith("(") or raw.strip().startswith("-")
    val = float(re.sub(r"[^\d.]", "", raw) or "nan")
    if raw.rstrip().endswith("%"):
        pass  # keep as given; both sides treated alike
    # scale words apply if they appear within 20 chars after the number
    tail = s[m.end():m.end() + 20]
    for rx, mult in _SCALE_WORDS:
        if rx.search(tail):
            val *= mult
            break
    return -val if neg else val


_UNIT_NOISE = re.compile(
    r"(usd|dollars?|million|billion|thousand|mn|bn|mm|approximately|about|around|roughly|~)",
    re.I,
)


def gold_is_numeric(gold: str) -> bool:
    """Gold counts as numeric when it is essentially just one number + units."""
    if not isinstance(gold, str):
        return False
    if len(_NUM_RE.findall(gold)) != 1:
        return False
    residue = _NUM_RE.sub("", gold)
    residue = _UNIT_NOISE.sub("", residue)
    residue = re.sub(r"[^A-Za-z]", "", residue)
    return len(residue) <= 8


_Q_UNIT = [
    (re.compile(r"billions?", re.I), 1e9),
    (re.compile(r"millions?", re.I), 1e6),
    (re.compile(r"thousands?", re.I), 1e3),
]


def question_unit(question: str) -> float:
    """Scale the question asks the answer in (FinanceBench golds use this unit)."""
    for rx, mult in _Q_UNIT:
        if rx.search(question or ""):
            return mult
    return 1.0


def _extract_raw(s: str):
    """Number without scale-word expansion."""
    m = _NUM_RE.search(s or "")
    if not m:
        return None
    raw = m.group(0)
    neg = raw.strip().startswith("(") or raw.strip().startswith("-")
    digits = re.sub(r"[^\d.]", "", raw)
    if not digits or digits == ".":
        return None
    val = float(digits)
    return -val if neg else val


def numeric_grade(gold: str, candidate: str, question: str = ""):
    """Returns (verdict, scale_error) for numeric-gold questions.

    Gold values are expressed in the question's implied unit (FinanceBench
    convention). Candidates may answer with explicit scale words or with the
    full absolute number, so we compare every reasonable interpretation of the
    candidate against the gold; a mismatch that is a clean power of ten is
    logged as a scale error (design.md v1.2e).
    """
    g = extract_number(gold)
    c_abs, c_raw = extract_number(candidate), _extract_raw(candidate)
    if g is None or c_abs is None:
        return "unparsed", False
    qm = question_unit(question)
    word_present = c_raw is not None and c_abs != c_raw
    interps = {c_abs}
    if word_present:
        if qm != 1.0:
            interps.add(c_abs / qm)
    else:
        if qm != 1.0:
            interps.add(c_abs / qm)
    if "%" in (gold or "") and "%" not in (candidate or ""):
        interps |= {i * 100 for i in list(interps)}  # 0.051 for gold "5.1%"
    if "%" in (candidate or "") and "%" not in (gold or "") and abs(g) < 1:
        interps |= {i / 100 for i in list(interps)}  # candidate "1.42%" for gold "0.01"
    # tolerance: 1% relative OR half a unit of the gold's last printed decimal
    # (golds like "0.01" are rounded per the question's instruction — v1.4)
    gm = _NUM_RE.search(gold)
    gdigits = gm.group(0) if gm else ""
    half_ulp = 0.5 * 10 ** -(len(gdigits.split(".")[1]) if "." in gdigits else 0)
    if g == 0:
        return ("correct" if any(abs(i) <= half_ulp for i in interps) else "incorrect"), False
    for i in interps:
        if abs(i - g) / abs(g) <= 0.01 or abs(i - g) <= half_ulp:
            return "correct", False
    for i in interps:
        if i == 0 or (i > 0) != (g > 0):
            continue
        for k in (1e2, 1e3, 1e6, 1e9):
            for ratio in (k, 1 / k):
                if abs(abs(i / g) - ratio) / ratio <= 0.02:
                    return "incorrect", True
    return "incorrect", False


def normalize_for_m3(s: str) -> str:
    return re.sub(r"[,$\s]", "", s)


def m3_evidence_presence(candidate_answer: str, evidence: str) -> bool:
    """Judge-free check: does the answer's number literally appear in the evidence
    (after normalization, incl. x1000 / x1e6 rescale and sign/parens variants)?"""
    val = extract_number(candidate_answer)
    if val is None:
        return False
    ev = normalize_for_m3(evidence)
    for scale in (1, 1e-3, 1e3, 1e-6, 1e6):
        v = val * scale
        for fmt in ("{:.0f}", "{:.1f}", "{:.2f}"):
            for sv in {v, -v}:
                s = fmt.format(sv)
                if s.lstrip("-").rstrip("0").rstrip(".") == "":
                    continue
                if s in ev or (s.startswith("-") and "(" + s[1:] + ")" in ev):
                    return True
    return False
