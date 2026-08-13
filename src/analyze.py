"""Full analysis from frozen CSVs only (hard rule 1). No API calls.

Reads:  results/raw_answers.csv, results/grades.csv, results/m2_agreement.csv,
        data/financebench.csv
Writes: results/metrics_summary.csv, results/conformal.csv, results/fsq_table.csv,
        results/figures/*.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grade_lib import m3_evidence_presence, gold_is_numeric
from prep_instances import oracle_evidence

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

SEED = 20260807
MODELS = ["haiku", "sonnet", "opus"]
TARGETS = [0.05, 0.10]

raw = pd.read_csv(ROOT / "results" / "raw_answers.csv")
_gf = ROOT / "results" / "grades_final.csv"
grades = pd.read_csv(_gf if _gf.exists() else ROOT / "results" / "grades.csv")
m2 = pd.read_csv(ROOT / "results" / "m2_agreement.csv", dtype={"qid": str})
master = raw.merge(grades[["custom_id", "grade_primary", "grade_method", "scale_error"]], on="custom_id")
master["correct"] = master.grade_primary == "correct"
master["qid"] = master.instance_id.str.split("-").str[1]

# ---- M3 (judge-free, computed here from frozen data)
fb_src = pd.read_csv(ROOT / "data" / "financebench.csv")
fb_src["qid"] = fb_src.financebench_id.str.replace("financebench_id_", "")
EVID = {r.qid: oracle_evidence(r.evidence) for _, r in fb_src.iterrows()}


def add_signals(fb_oracle: pd.DataFrame) -> pd.DataFrame:
    d = fb_oracle.copy()
    m2k = m2.set_index(["qid", "model"]).agree
    d["m2_agree"] = [bool(m2k.get((q, m), False)) for q, m in zip(d.qid, d.model)]
    d["m3_present"] = [
        (not r.refused) and m3_evidence_presence(str(r.answer), EVID[r.qid])
        for _, r in d.iterrows()
    ]
    d["gold_numeric"] = d.gold_answer.astype(str).map(gold_is_numeric)
    return d


def sel_metrics(d, mask, n_total):
    sel = d[mask & ~d.refused]
    cov = len(sel) / n_total
    risk = float((~sel.correct).mean()) if len(sel) else np.nan
    return cov, risk, len(sel)


def m1_curve(d, n_total):
    """(threshold, coverage, risk) rows, descending confidence."""
    confs = sorted(d.loc[~d.refused, "confidence"].dropna().unique(), reverse=True)
    rows = []
    for t in confs:
        cov, risk, n = sel_metrics(d, d.confidence >= t, n_total)
        rows.append({"threshold": t, "coverage": cov, "risk": risk, "n": n})
    return pd.DataFrame(rows)


def aurc(curve: pd.DataFrame) -> float:
    if len(curve) < 2:
        return np.nan
    c = curve.sort_values("coverage")
    return float(np.trapz(c.risk, c.coverage) / (c.coverage.max() - c.coverage.min() + 1e-12))


def ece(d, bins=10):
    a = d[~d.refused & d.confidence.notna()]
    if a.empty:
        return np.nan
    conf = a.confidence / 100.0
    err = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        m = (conf >= lo) & (conf < lo + 1 / bins + (1e-9 if lo + 1 / bins >= 1 else 0))
        if m.sum():
            err += m.mean() * abs(conf[m].mean() - a.correct[m].mean())
    return float(err)


def conformal(d, method, target, n_total_half):
    """Split by qid (seeded); tune smallest threshold; prove realized risk + bootstrap CI."""
    rng = np.random.RandomState(SEED)
    qids = sorted(d.qid.unique())
    perm = rng.permutation(qids)
    tune_q, prove_q = set(perm[: len(perm) // 2]), set(perm[len(perm) // 2:])
    tune, prove = d[d.qid.isin(tune_q)], d[d.qid.isin(prove_q)]

    def select(frame, thr):
        if method == "M1":
            return frame[~frame.refused & frame.confidence.notna() & (frame.confidence >= thr)]
        if method == "M2":
            return frame[~frame.refused & frame.m2_agree]
        if method == "M3":
            return frame[~frame.refused & frame.m3_present]

    thr_star = None
    if method == "M1":
        for t in sorted(tune.loc[~tune.refused, "confidence"].dropna().unique()):
            s = select(tune, t)
            if len(s) and (~s.correct).mean() <= target:
                thr_star = t
                break
        if thr_star is None:
            return {"threshold": None, "tune_risk": None, "coverage": 0.0,
                    "realized_risk": None, "ci_lo": None, "ci_hi": None, "held": False}
        s_tune = select(tune, thr_star)
    else:
        s_tune = select(tune, None)
        if not len(s_tune) or (~s_tune.correct).mean() > target:
            return {"threshold": "signal", "tune_risk": float((~s_tune.correct).mean()) if len(s_tune) else None,
                    "coverage": 0.0, "realized_risk": None, "ci_lo": None, "ci_hi": None, "held": False}
        thr_star = "signal"

    s = select(prove, thr_star if method == "M1" else None)
    n_half = len(prove.qid.unique())
    coverage = len(s) / n_half
    realized = float((~s.correct).mean()) if len(s) else np.nan
    boots = []
    brng = np.random.RandomState(SEED + 1)
    vals = (~s.correct).astype(int).values
    for _ in range(1000):
        if len(vals) == 0:
            break
        boots.append(brng.choice(vals, size=len(vals), replace=True).mean())
    lo, hi = (np.percentile(boots, [2.5, 97.5]) if boots else (np.nan, np.nan))
    held = bool(realized <= target or (lo <= target <= hi)) if len(s) else False
    return {"threshold": thr_star, "tune_risk": float((~s_tune.correct).mean()),
            "coverage": coverage, "realized_risk": realized,
            "ci_lo": float(lo), "ci_hi": float(hi), "held": held}


def coverage_at_risk(curve, target):
    ok = curve[curve.risk <= target]
    return float(ok.coverage.max()) if len(ok) else 0.0


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary, conf_rows = [], []
    fb = master[(master.dataset == "financebench")]
    for model in MODELS:
        for setting in ["oracle", "closedbook"]:
            d = fb[(fb.model == model) & (fb.setting == setting)]
            n = len(d)
            summary += [
                dict(model=model, setting=setting, metric="n", value=n),
                dict(model=model, setting=setting, metric="accuracy_all", value=d.correct.mean()),
                dict(model=model, setting=setting, metric="refusal_rate", value=d.refused.mean()),
                dict(model=model, setting=setting, metric="accuracy_answered",
                     value=d[~d.refused].correct.mean() if (~d.refused).any() else np.nan),
                dict(model=model, setting=setting, metric="scale_error_rate", value=d.scale_error.mean()),
            ]
        # oracle-only selective analysis
        d = add_signals(fb[(fb.model == model) & (fb.setting == "oracle")])
        n = len(d)
        curve = m1_curve(d, n)
        curve.to_csv(ROOT / "results" / f"m1_curve_{model}.csv", index=False)
        summary += [
            dict(model=model, setting="oracle", metric="aurc_m1", value=aurc(curve)),
            dict(model=model, setting="oracle", metric="ece_m1", value=ece(d)),
        ]
        for tgt in TARGETS:
            summary.append(dict(model=model, setting="oracle",
                                metric=f"coverage_at_{int(tgt*100)}pct_risk_full", value=coverage_at_risk(curve, tgt)))
        cov2, risk2, _ = sel_metrics(d, d.m2_agree, n)
        cov3, risk3, _ = sel_metrics(d, d.m3_present, n)
        summary += [
            dict(model=model, setting="oracle", metric="m2_coverage", value=cov2),
            dict(model=model, setting="oracle", metric="m2_risk", value=risk2),
            dict(model=model, setting="oracle", metric="m3_coverage", value=cov3),
            dict(model=model, setting="oracle", metric="m3_risk", value=risk3),
        ]
        for method in ["M1", "M2", "M3"]:
            for tgt in TARGETS:
                r = conformal(d, method, tgt, n // 2)
                conf_rows.append(dict(model=model, method=method, target=tgt, **r))

        # figures: risk-coverage + reliability
        plt.figure(figsize=(5.2, 4.2))
        plt.plot(curve.coverage, curve.risk, "-o", ms=3, label="M1 verbalized conf")
        plt.scatter([cov2], [risk2], marker="s", c="tab:orange", zorder=5, label="M2 self-agreement")
        plt.scatter([cov3], [risk3], marker="^", c="tab:green", zorder=5, label="M3 evidence-presence")
        for tgt, ls in zip(TARGETS, [":", "--"]):
            plt.axhline(tgt, ls=ls, c="gray", lw=1)
        plt.xlabel("coverage (fraction of 150 answered)")
        plt.ylabel("risk (error rate among answered)")
        plt.title(f"Risk-coverage - {model} (FinanceBench oracle)")
        plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(FIG / f"risk_coverage_{model}.png", dpi=150); plt.close()

        a = d[~d.refused & d.confidence.notna()]
        bins = np.linspace(0, 100, 11)
        mids, accs, cnts = [], [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (a.confidence >= lo) & (a.confidence < hi if hi < 100 else a.confidence <= 100)
            if m.sum():
                mids.append((lo + hi) / 2); accs.append(a.correct[m].mean()); cnts.append(int(m.sum()))
        plt.figure(figsize=(5.2, 4.2))
        plt.plot([0, 100], [0, 1], "k--", lw=1, label="perfect calibration")
        plt.plot(mids, accs, "o-", label="observed")
        for x, y, c in zip(mids, accs, cnts):
            plt.annotate(str(c), (x, y), fontsize=7, xytext=(0, 6), textcoords="offset points", ha="center")
        plt.xlabel("stated confidence"); plt.ylabel("fraction correct")
        plt.title(f"Calibration - {model} (FinanceBench oracle)")
        plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(FIG / f"calibration_{model}.png", dpi=150); plt.close()

    # ---- FailSafeQA table
    fsq = master[master.dataset == "failsafeqa"]
    fsq_rows = []
    for model in MODELS:
        d = fsq[fsq.model == model]
        base = d[d.setting == "base"]
        pert = d[d.setting == "pert"]
        unans = d[d.setting == "unans"]
        row = dict(model=model,
                   base_accuracy=base.correct.mean(),
                   base_refusal=base.refused.mean(),
                   robustness_all=pert.correct.mean(),
                   compliance_all=unans.refused.mean(),
                   hallucination_on_unanswerable=1 - unans.refused.mean())
        for v in ["misspelled", "incomplete", "outofdomain", "ocr"]:
            row[f"rob_{v}"] = pert[pert.variant == v].correct.mean()
        for v in ["missingctx", "outofscope"]:
            row[f"comp_{v}"] = unans[unans.variant == v].refused.mean()
        ans_unans = unans[~unans.refused]
        row["mean_conf_when_guessing"] = ans_unans.confidence.mean()
        row["mean_conf_base_correct"] = base[base.correct].confidence.mean()
        fsq_rows.append(row)
    fsq_table = pd.DataFrame(fsq_rows)
    fsq_table.to_csv(ROOT / "results" / "fsq_table.csv", index=False)

    labels = ["Haiku 4.5", "Sonnet 5", "Opus 5"]
    x = np.arange(3)
    plt.figure(figsize=(6.4, 4.2))
    w = 0.35
    plt.bar(x - w / 2, fsq_table.robustness_all, w, label="Robustness (acc. on perturbed)")
    plt.bar(x + w / 2, fsq_table.compliance_all, w, label="Compliance (refusal on unanswerable)")
    plt.xticks(x, labels); plt.ylim(0, 1); plt.ylabel("rate")
    plt.title("FailSafeQA: robustness vs compliance")
    plt.legend(fontsize=8); plt.grid(alpha=0.3, axis="y"); plt.tight_layout()
    plt.savefig(FIG / "fsq_robustness_compliance.png", dpi=150); plt.close()

    pd.DataFrame(summary).to_csv(ROOT / "results" / "metrics_summary.csv", index=False)
    cf = pd.DataFrame(conf_rows)
    cf.to_csv(ROOT / "results" / "conformal.csv", index=False)
    print("metrics_summary.csv, conformal.csv, fsq_table.csv, figures/ written")
    print("\n== headline ==")
    print(pd.DataFrame(summary).pivot_table(index=["model", "setting"], columns="metric", values="value").round(3).to_string())
    print("\n== conformal ==")
    print(cf.round(3).to_string())
    print("\n== fsq ==")
    print(fsq_table.round(3).to_string())


if __name__ == "__main__":
    main()
