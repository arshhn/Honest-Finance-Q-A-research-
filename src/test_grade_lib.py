"""Offline validation of parsing/grading. Run: python test_grade_lib.py"""
from grade_lib import (extract_number, gold_is_numeric, m3_evidence_presence,
                       numeric_grade, parse_response)

failures = []


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'} {name}: got={got!r} want={want!r}")
    if not ok:
        failures.append(name)


# --- parse_response
a, c, r, ok = parse_response("ANSWER: $1,577 million\nCONFIDENCE: 95")
check("parse.answer", a, "$1,577 million"); check("parse.conf", c, 95); check("parse.refused", r, False)
_, c, r, ok = parse_response("ANSWER: CANNOT ANSWER\nCONFIDENCE: 20")
check("parse.refusal", r, True)
_, _, r, ok = parse_response("I cannot answer based on this document.")
check("parse.freeform-refusal", r, True); check("parse.freeform-notok", ok, False)

# --- extract_number
check("num.commas", extract_number("$1,577 million"), 1577e6)
check("num.scaleword", extract_number("1.577 billion USD"), 1.577e9)
check("num.paren-neg", extract_number("(1,577)"), -1577.0)
check("num.pct", extract_number("5.1%"), 5.1)

# --- gold_is_numeric routing
check("goldnum.plain", gold_is_numeric("$1577.00"), True)
check("goldnum.units", gold_is_numeric("$8.70 billion"), True)
check("goldnum.sentence", gold_is_numeric("Yes, they have increased dividends for 65 consecutive years"), False)
check("goldnum.multi", gold_is_numeric("CAPEX 5.1% and ROA 12.4%"), False)

# --- numeric_grade: (gold, candidate, question) -> (verdict, scale_err)
Q_M = "What is the FY2018 capital expenditure (in USD millions)?"
Q_B = "What is the year end FY2018 net PPNE? Answer in USD billions."
check("grade.units-vs-implied", numeric_grade("$1577.00", "$1,577 million", Q_M), ("correct", False))
check("grade.plain-in-q-units", numeric_grade("$1577.00", "ANSWER: 1,577", Q_M), ("correct", False))
check("grade.within-1pct", numeric_grade("$1577.00", "$1,580 million", Q_M), ("correct", False))
check("grade.wrong", numeric_grade("$1577.00", "$1,700 million", Q_M), ("incorrect", False))
check("grade.billions", numeric_grade("$8.70", "8,738 million dollars", Q_B), ("correct", False))
check("grade.scale-err", numeric_grade("$8.70", "8,738", Q_B), ("incorrect", True))
check("grade.pct", numeric_grade("5.1%", "5.1%", "capex ratio?"), ("correct", False))
check("grade.pct-fraction", numeric_grade("5.1%", "0.051", "capex ratio?"), ("correct", False))
check("grade.absolute-full", numeric_grade("$1577.00", "$1,577,000,000", Q_M), ("correct", False))

# --- M3
check("m3.hit", m3_evidence_presence("$1,577 million", "Purchases of PP&E  (1,577)  x"), True)
check("m3.miss", m3_evidence_presence("999 million", "total 1,577 here"), False)
# M3 is a LITERAL check by design (v1.2g): a rounded answer (8.7bn vs 8,738m) does NOT count
check("m3.rounded-misses", m3_evidence_presence("$8.7 billion", "PP&E net 8,738 "), False)
check("m3.exact-scaled", m3_evidence_presence("$8,738 million", "PP&E net 8,738 "), True)

print()
if failures:
    print(f"{len(failures)} FAILURES: {failures}")
    raise SystemExit(1)
print("ALL PASS")
