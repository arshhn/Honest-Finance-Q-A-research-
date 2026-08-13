"""Full analysis from frozen CSVs only (hard rule 1). No API calls.

v2 (rulebook v1.8, post internal review): exact Clopper-Pearson intervals; a
certified (finite-sample-bounded) threshold rule alongside the pre-registered
plug-in rule; M2 restricted to context-independent pairs; M3 restricted to its
pre-registered numeric-gold scope; matched-coverage risk replaces span-normalised
AURC; multi-seed split sensitivity; corrected FSQ denominators with exact bounds.

Reads:  results/raw_answers.csv, results/grades_final.csv (fallback grades.csv),
        results/m2_agreement.csv, data/financebench.csv
Writes: results/metrics_summary.csv, results/conformal.csv, results/fsq_table.csv,
        results/multiseed.csv, results/figures/*.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grade_lib import m3_evidence_presence, gold_is_numeric
from prep_instances import oracle_evidence

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

SEED = 20260807
MODELS = ["haiku", "sonnet", "opus"]
TARGETS = [0.05, 0.10]
N_SENS_SEEDS = 200

raw = pd.read_csv(ROOT / "results" / "raw_answers.csv")
_gf = ROOT / "results" / "grades_final.csv"
grades = pd.read_csv(_gf if _gf.exists() else ROOT / "results" / "grades.csv")
grades_orig = pd.read_csv(ROOT / "results" / "grades.csv")
m2 = pd.read_csv(ROOT / "results" / "m2_agreement.csv", dtype={"qid": str})
master = raw.merge(grades[["custom_id", "grade_primary", "grade_method", "scale_error"]], on="custom_id")
master["correct"] = master.grade_primary == "correct"
master["qid"] = master.instance_id.str.split("-").str[1]

fb_src = pd.read_csv(ROOT / "data" / "financebench.csv")
fb_src["qid"] = fb_src.financebench_id.str.replace("financebench_id_", "")
EVID = {r.qid: oracle_evidence(r.evidence) for _, r in fb_src.iterrows()}


# ---------- exact binomial machinery ----------
def cp_interval(k, n, alpha=0.05):
    """Two-sided Clopper-Pearson."""
    if n == 0:
        return (np.nan, np.nan)
    lo = 0.0 if k == 0 else float(beta_dist.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta_dist.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def cp_upper(k, n, conf=0.95):
    """One-sided exact upper bound on a proportion."""
    if n == 0:
        return np.nan
    return 1.0 if k == n else float(beta_dist.ppf(conf, k + 1, n - k))


# ---------- M2 (context-independent pairs only) ----------
def m2_clean_table():
    """agree per (qid, model), excluding pairs whose oracle+para sittings shared
    one context window (v1.5 batching side-effect; rulebook v1.8)."""
    fb = raw[(raw.dataset == "financebench") & raw.setting.isin(["oracle", "para"])].copy()
    fb["qid"] = fb.instance_id.str.split("-").str[1]
    b = fb.pivot_table(index=["qid", "model"], columns="setting", values="batch_id",
                       aggfunc="first")
    b["same_window"] = (b.oracle.fillna("").astype(str) != "") & (b.oracle == b.para)
    out = m2.merge(b.reset_index()[["qid", "model", "same_window"]], on=["qid", "model"], how="left")
    out["same_window"] = out.same_window.fillna(False)
    out["agree"] = out.agree.astype(float)
    return out


M2C = m2_clean_table()


def add_signals(fb_oracle: pd.DataFrame) -> pd.DataFrame:
    d = fb_oracle.copy()
    key = M2C.set_index(["qid", "model"])
    d["m2_valid"] = [not bool(key.loc[(q, m)].same_window) if (q, m) in key.index else False
                     for q, m in zip(d.qid, d.model)]
    d["m2_agree"] = [bool(key.loc[(q, m)].agree) if (q, m) in key.index else False
                     for q, m in zip(d.qid, d.model)]
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
    confs = sorted(d.loc[~d.refused, "confidence"].dropna().unique(), reverse=True)
    rows = []
    for t in confs:
        cov, risk, n = sel_metrics(d, d.confidence >= t, n_total)
        rows.append({"threshold": t, "coverage": cov, "risk": risk, "n": n})
    return pd.DataFrame(rows)


def matched_coverage_risk(curve, levels=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    """Mean of the minimum achievable risk at coverage >= each level (comparable
    across models, unlike span-normalised AURC)."""
    vals = []
    for lv in levels:
        c = curve[curve.coverage >= lv]
        if len(c):
            vals.append(c.risk.min())
    return float(np.mean(vals)) if vals else np.nan


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


def split_qids(d, seed):
    rng = np.random.RandomState(seed)
    qids = sorted(d.qid.unique())
    perm = rng.permutation(qids)
    return set(perm[: len(perm) // 2]), set(perm[len(perm) // 2:])


def select_rows(frame, method, thr):
    if method == "M1":
        return frame[~frame.refused & frame.confidence.notna() & (frame.confidence >= thr)]
    if method == "M2":
        return frame[frame.m2_valid & ~frame.refused & frame.m2_agree]
    if method == "M3":
        return frame[frame.gold_numeric & ~frame.refused & frame.m3_present]


def eligible(frame, method):
    """Population a signal is defined on (denominator for coverage)."""
    if method == "M1":
        return frame
    if method == "M2":
        return frame[frame.m2_valid]
    if method == "M3":
        return frame[frame.gold_numeric]


def pick_threshold(tune, method, target, rule):
    """plugin: smallest t with empirical tune risk <= target (pre-registered).
    certified: smallest t whose one-sided 95% CP upper bound on tune risk <= target."""
    if method != "M1":
        s = select_rows(tune, method, None)
        k, n = int((~s.correct).sum()), len(s)
        ok = (n > 0) and ((k / n <= target) if rule == "plugin" else (cp_upper(k, n) <= target))
        return ("signal" if ok else None), (k / n if n else np.nan)
    for t in sorted(tune.loc[~tune.refused, "confidence"].dropna().unique()):
        s = select_rows(tune, "M1", t)
        k, n = int((~s.correct).sum()), len(s)
        if n == 0:
            continue
        ok = (k / n <= target) if rule == "plugin" else (cp_upper(k, n) <= target)
        if ok:
            return t, k / n
    return None, np.nan


def conformal_row(d, method, target, rule, seed=SEED):
    tune_q, prove_q = split_qids(d, seed)
    tune, prove = d[d.qid.isin(tune_q)], d[d.qid.isin(prove_q)]
    thr, tune_risk = pick_threshold(tune, method, target, rule)
    base = {"threshold": thr, "tune_risk": tune_risk, "coverage": 0.0, "n_answered": 0,
            "n_excluded_by_threshold": 0, "realized_risk": np.nan,
            "cp_lo": np.nan, "cp_hi": np.nan, "degenerate": True}
    if thr is None:
        return base
    s = select_rows(prove, method, thr if method == "M1" else None)
    elig = eligible(prove, method)
    n_elig = len(elig.qid.unique())
    nonref = elig[~elig.refused] if method != "M1" else prove[~prove.refused & prove.confidence.notna()]
    k, n = int((~s.correct).sum()), len(s)
    lo, hi = cp_interval(k, n)
    base.update(coverage=n / max(1, n_elig), n_answered=n,
                n_excluded_by_threshold=len(nonref) - n,
                realized_risk=(k / n if n else np.nan),
                cp_lo=lo, cp_hi=hi, degenerate=n < 20)
    return base


def multiseed(d, method, target, rule, n_seeds=N_SENS_SEEDS):
    covs, risks, met = [], [], 0
    for s in range(n_seeds):
        r = conformal_row(d, method, target, rule, seed=SEED + 1000 + s)
        if r["threshold"] is None or r["n_answered"] == 0:
            covs.append(0.0); continue
        covs.append(r["coverage"]); risks.append(r["realized_risk"])
        if r["realized_risk"] <= target:
            met += 1
    q = lambda a, p: float(np.percentile(a, p)) if a else np.nan
    return {"cov_med": q(covs, 50), "cov_iqr_lo": q(covs, 25), "cov_iqr_hi": q(covs, 75),
            "risk_med": q(risks, 50), "risk_iqr_lo": q(risks, 25), "risk_iqr_hi": q(risks, 75),
            "frac_runs_at_or_under_target": (met / n_seeds)}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary, conf_rows, sens_rows = [], [], []
    fb = master[(master.dataset == "financebench")]
    adjudicated = set(grades[grades.grade_method == "adjudicated"].custom_id) if "grade_method" in grades else set()

    for model in MODELS:
        for setting in ["oracle", "closedbook"]:
            d = fb[(fb.model == model) & (fb.setting == setting)]
            n = len(d)
            acc_k = int(d.correct.sum())
            summary += [
                dict(model=model, setting=setting, metric="n", value=n),
                dict(model=model, setting=setting, metric="accuracy_all", value=d.correct.mean()),
                dict(model=model, setting=setting, metric="accuracy_all_cp_lo", value=cp_interval(acc_k, n)[0]),
                dict(model=model, setting=setting, metric="accuracy_all_cp_hi", value=cp_interval(acc_k, n)[1]),
                dict(model=model, setting=setting, metric="refusal_rate", value=d.refused.mean()),
                dict(model=model, setting=setting, metric="accuracy_answered",
                     value=d[~d.refused].correct.mean() if (~d.refused).any() else np.nan),
                dict(model=model, setting=setting, metric="scale_error_rate", value=d.scale_error.mean()),
            ]
        d = add_signals(fb[(fb.model == model) & (fb.setting == "oracle")])
        n = len(d)
        curve = m1_curve(d, n)
        curve.to_csv(ROOT / "results" / f"m1_curve_{model}.csv", index=False)
        summary += [
            dict(model=model, setting="oracle", metric="matched_cov_risk_m1", value=matched_coverage_risk(curve)),
            dict(model=model, setting="oracle", metric="ece_m1_deciles", value=ece(d)),
            dict(model=model, setting="oracle", metric="m2_valid_pairs", value=int(d.m2_valid.sum())),
            dict(model=model, setting="oracle", metric="m3_eligible", value=int(d.gold_numeric.sum())),
        ]
        for tgt in TARGETS:
            ok = curve[curve.risk <= tgt]
            summary.append(dict(model=model, setting="oracle",
                                metric=f"coverage_at_{int(tgt*100)}pct_risk_insample", value=float(ok.coverage.max()) if len(ok) else 0.0))
        # signal operating points on their eligible populations
        e2 = eligible(d, "M2"); s2 = select_rows(d, "M2", None)
        e3 = eligible(d, "M3"); s3 = select_rows(d, "M3", None)
        summary += [
            dict(model=model, setting="oracle", metric="m2_coverage_eligible", value=len(s2) / max(1, len(e2))),
            dict(model=model, setting="oracle", metric="m2_risk", value=float((~s2.correct).mean()) if len(s2) else np.nan),
            dict(model=model, setting="oracle", metric="m3_coverage_eligible", value=len(s3) / max(1, len(e3))),
            dict(model=model, setting="oracle", metric="m3_risk", value=float((~s3.correct).mean()) if len(s3) else np.nan),
        ]
        for method in ["M1", "M2", "M3"]:
            for tgt in TARGETS:
                for rule in ["plugin", "certified"]:
                    r = conformal_row(d, method, tgt, rule)
                    conf_rows.append(dict(model=model, method=method, target=tgt, rule=rule, **r))
                ms = multiseed(d, method, tgt, "plugin")
                sens_rows.append(dict(model=model, method=method, target=tgt, rule="plugin", **ms))

        plt.figure(figsize=(5.2, 4.2))
        plt.plot(curve.coverage, curve.risk, "-o", ms=3, label="M1 verbalized conf")
        if len(s2):
            plt.scatter([len(s2) / max(1, len(e2))], [float((~s2.correct).mean())], marker="s",
                        c="tab:orange", zorder=5, label=f"M2 self-agreement (n={len(e2)})")
        if len(s3):
            plt.scatter([len(s3) / max(1, len(e3))], [float((~s3.correct).mean())], marker="^",
                        c="tab:green", zorder=5, label=f"M3 evidence-presence (n={len(e3)})")
        for tgt, ls in zip(TARGETS, [":", "--"]):
            plt.axhline(tgt, ls=ls, c="gray", lw=1)
        plt.xlabel("coverage (fraction of eligible questions answered)")
        plt.ylabel("risk (error rate among answered)")
        plt.title(f"Risk-coverage - {model} (FinanceBench oracle)")
        plt.legend(fontsize=7); plt.grid(alpha=0.3); plt.tight_layout()
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
        plt.plot(mids, accs, "o-", label="observed (decile bins)")
        for x, y, c in zip(mids, accs, cnts):
            plt.annotate(str(c), (x, y), fontsize=7, xytext=(0, 6), textcoords="offset points", ha="center")
        plt.xlabel("stated confidence"); plt.ylabel("fraction correct")
        plt.title(f"Calibration - {model} (bin counts shown; n={len(a)})")
        plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(FIG / f"calibration_{model}.png", dpi=150); plt.close()

    # adjudication sensitivity: recompute headline conformal rows on original grades
    master_orig = raw.merge(grades_orig[["custom_id", "grade_primary"]], on="custom_id")
    master_orig["correct"] = master_orig.grade_primary == "correct"
    master_orig["qid"] = master_orig.instance_id.str.split("-").str[1]
    for model in MODELS:
        d0 = add_signals(master_orig[(master_orig.dataset == "financebench")
                                     & (master_orig.model == model)
                                     & (master_orig.setting == "oracle")])
        r = conformal_row(d0, "M1", 0.10, "plugin")
        conf_rows.append(dict(model=model, method="M1", target=0.10, rule="plugin_preadjudication", **r))

    # ---- FailSafeQA (corrected denominators + exact bounds)
    fsq = master[master.dataset == "failsafeqa"]
    fsq_rows = []
    pooled_unans_k = pooled_unans_n = 0
    for model in MODELS:
        d = fsq[fsq.model == model]
        base = d[d.setting == "base"]; pert = d[d.setting == "pert"]; unans = d[d.setting == "unans"]
        k_fab = int((~unans.refused).sum())
        pooled_unans_k += k_fab; pooled_unans_n += len(unans)
        row = dict(model=model,
                   n_base=len(base), n_pert=len(pert), n_unans=len(unans),
                   base_accuracy=base.correct.mean(), base_refusal=base.refused.mean(),
                   robustness_all=pert.correct.mean(),
                   robustness_cp_lo=cp_interval(int(pert.correct.sum()), len(pert))[0],
                   compliance_all=unans.refused.mean(),
                   fabrication=k_fab / max(1, len(unans)),
                   fabrication_cp_upper95=cp_upper(k_fab, len(unans)))
        for v in ["misspelled", "incomplete", "outofdomain", "ocr"]:
            sub = pert[pert.variant == v]
            row[f"rob_{v}"] = sub.correct.mean(); row[f"n_{v}"] = len(sub)
        for v in ["missingctx", "outofscope"]:
            sub = unans[unans.variant == v]
            row[f"comp_{v}"] = sub.refused.mean(); row[f"n_{v}"] = len(sub)
        fsq_rows.append(row)
    fsq_table = pd.DataFrame(fsq_rows)
    fsq_table.attrs["pooled_fabrication"] = (pooled_unans_k, pooled_unans_n,
                                             cp_upper(pooled_unans_k, pooled_unans_n))
    fsq_table.to_csv(ROOT / "results" / "fsq_table.csv", index=False)

    labels = ["Haiku 4.5", "Sonnet 5", "Opus 5"]
    x = np.arange(3); w = 0.35
    plt.figure(figsize=(6.4, 4.2))
    plt.bar(x - w / 2, fsq_table.robustness_all, w, label="Robustness (acc. on perturbed)")
    plt.bar(x + w / 2, fsq_table.compliance_all, w, label="Compliance (refusal on unanswerable)")
    for i, r in fsq_table.iterrows():
        plt.text(x[i] - w / 2, r.robustness_all + .01, f"n={r.n_pert}", ha="center", fontsize=7)
        plt.text(x[i] + w / 2, r.compliance_all + .01, f"n={r.n_unans}", ha="center", fontsize=7)
    plt.xticks(x, labels); plt.ylim(0, 1.12); plt.ylabel("rate")
    plt.title("FailSafeQA seeded subset: robustness vs compliance")
    plt.legend(fontsize=8); plt.grid(alpha=0.3, axis="y"); plt.tight_layout()
    plt.savefig(FIG / "fsq_robustness_compliance.png", dpi=150); plt.close()

    pd.DataFrame(summary).to_csv(ROOT / "results" / "metrics_summary.csv", index=False)
    cf = pd.DataFrame(conf_rows); cf.to_csv(ROOT / "results" / "conformal.csv", index=False)
    sn = pd.DataFrame(sens_rows); sn.to_csv(ROOT / "results" / "multiseed.csv", index=False)
    print("metrics_summary.csv, conformal.csv, multiseed.csv, fsq_table.csv, figures/ written")
    print("\n== headline ==")
    print(pd.DataFrame(summary).pivot_table(index=["model", "setting"], columns="metric", values="value").round(3).to_string())
    print("\n== conformal (seed 20260807) ==")
    print(cf.round(3).to_string())
    print("\n== multiseed sensitivity (200 seeds, plugin) ==")
    print(sn.round(3).to_string())
    print("\n== fsq ==")
    print(fsq_table.round(3).to_string())
    print("\npooled fabrication k/n + CP95 upper:", fsq_table.attrs["pooled_fabrication"])


if __name__ == "__main__":
    main()
