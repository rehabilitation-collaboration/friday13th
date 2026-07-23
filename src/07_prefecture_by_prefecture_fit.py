"""07_prefecture_by_prefecture_fit.py

Phase 2C-C4:
Prefecture-by-prefecture NB fit for the Figure S3 forest plot. Each of the 47
prefectures reuses the **mean model** from ``03_prefecture_panel_weather_nb.py``
(2C-C2-e primary — weather+holiday+cloud with year/month/weekday FE), but the
**SE method necessarily differs**: prefecture FE is dropped (single-prefecture
subset) and each date appears in exactly one row of the subset, so the panel's
two-way cluster (prefecture, date) construction is not available. Standard
errors are therefore heteroscedasticity-robust HC1 (Cameron & Miller 2015
Section 3.4 default when clustering is not identified inside a stratum).

Design notes
------------
  + **SE method = HC1** (2C-C4 MAGI-AKAGI P1 fix): 07 originally requested
    `cov_type='cluster'` with date as the grouping variable, but within a
    single-prefecture subset every date has exactly one observation, so the
    sandwich meat sum collapses to the plain HC0 meat sum. Empirically, the
    statsmodels cluster path returns HC0 × sqrt((G/(G-1))×((N-1)/(N-K)))
    ≈ HC0 × 1.008 for G=N=2192, K≈32. Reporting this as "cluster SE" would
    misdescribe the estimator to referees. HC1 (heteroscedasticity-robust
    with (N/(N-K)) finite-sample scaling) is the correct label.
  + **Zero-variance weather covariates** are dropped per prefecture. Six
    prefectures (Kagawa, Miyazaki, Oita, Okinawa, Osaka, Shizuoka) have
    snowfall_cm=0 and snow_depth_max_cm=0 for the whole 2019-2024 window;
    including them as regressors triggers a rank deficiency in the design
    matrix. precipitation_mm has non-zero variance in every prefecture.
  + **Pairwise-collinear weather covariates** are dropped per prefecture
    (2C-C4 MAGI-AKAGI P2 fix, 3/3 vote): Ehime (1 snow day) and Okayama
    (2 snow days) have corr(snowfall_cm, snow_depth_max_cm) = 1.000000 in
    the subset, and originally failed at the Poisson warm start with
    `LinAlgError: Singular matrix`. `_find_pairwise_collinear(threshold=0.999)`
    drops one column of each perfect pair, recovering these 2 prefectures for
    the forest plot.
  + **Non-convergence** is a flag, not a raise. The forest plot annotates
    non-converged prefectures instead of failing the whole run.

Model per prefecture
--------------------
  endog = total_count
  exog  = is_fri13 + is_13th
          + is_holiday + is_obon + is_newyear
          + cloud_cover + precipitation_mm
          [+ snowfall_cm]        (dropped if std=0 or pairwise-collinear)
          [+ snow_depth_max_cm]  (dropped if std=0 or pairwise-collinear)
          + year FE + month FE + weekday FE
  loglike_method = 'nb2'; Poisson warm start; MLE alpha; HC1 robust SE.

Outputs
-------
  output/prefecture_irr_by_prefecture.json
    schema:
      project, phase, generated, script, model_notes,
      values: [ _v() summary entries — counts, ratio extrema, multi-test disclosure ],
      diagnostics: {
        n_prefectures, n_converged, n_non_converged, n_listwise_dropped,
        dropped_covariates_by_prefecture: {pref: [dropped_cols]},
        results: [
          {prefecture_en, converged, non_conv_reason, n_obs,
           dropped_covariates, dropped_reason,
           is_fri13_coef, is_fri13_se, is_fri13_p,
           count_ratio, count_ratio_ci_low, count_ratio_ci_high,
           alpha_mle_nb2, se_source, nb2_runtime_warnings}
        ]
      }
"""
from __future__ import annotations

import json
import math
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as scipy_stats
from statsmodels.discrete.discrete_model import NegativeBinomial

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
DATA = ROOT / "data" / "processed"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# Ensure src/ is on sys.path for CLI execution (pytest handles via conftest).
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PREF_ACC = DATA / "accidents_by_prefecture_daily.parquet"
PREF_CLD = DATA / "cloud_by_prefecture_daily.parquet"
PREF_WTH = DATA / "weather_by_prefecture_daily.parquet"

OUT_JSON = OUTPUT / "prefecture_irr_by_prefecture.json"

DUMMY_COLS = ("year", "month", "weekday")  # NO prefecture FE (single-subset)
WEATHER_COLS = ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")
BASE_MAIN_EFFECTS = (
    "is_fri13",
    "is_13th",
    "is_holiday",
    "is_obon",
    "is_newyear",
    "cloud_cover",
    "precipitation_mm",
    "snowfall_cm",
    "snow_depth_max_cm",
)

# 95% CI z-critical + safe conversions unified via _stats_helpers.py
# (2C-C4 D1+D4 fix: eliminates 3-form Z drift and 3-copy safe-helper duplication).
from _stats_helpers import (  # noqa: E402
    Z_CRIT_95 as Z95,
    safe_exp as _safe_exp,
    safe_float as _safe_float,
)

COLLINEARITY_THRESHOLD = 0.999  # pairwise |corr| above this triggers drop of one column


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_prefecture_panel() -> tuple[pd.DataFrame, int]:
    """(date, prefecture_en) panel joined with cloud_cover + weather.

    Mirrors 03_prefecture_panel_weather_nb.load_prefecture_panel semantics:
    cloud NaN -> panel median (panel-wide, not per-prefecture — same choice
    as 03), weather NaN -> listwise deletion.

    Returns (df, n_listwise_dropped) so the caller can surface the drop count
    in the JSON diagnostics (03 prints it to stdout; 07 persists it).
    """
    acc = pd.read_parquet(PREF_ACC)
    cld = pd.read_parquet(PREF_CLD)[["date", "prefecture_en", "cloud_cover"]]
    wth = pd.read_parquet(PREF_WTH)[["date", "prefecture_en", *WEATHER_COLS]]
    df = (
        acc.merge(cld, on=["date", "prefecture_en"], how="left")
           .merge(wth, on=["date", "prefecture_en"], how="left")
    )
    med = df["cloud_cover"].median()
    df["cloud_cover"] = df["cloud_cover"].fillna(med).astype(float)
    before = len(df)
    weather_na = df[list(WEATHER_COLS)].isna().any(axis=1)
    n_dropped = int(weather_na.sum())
    df = df.loc[~weather_na].copy()
    for c in WEATHER_COLS:
        df[c] = df[c].astype(float)
    if n_dropped:
        print(
            f"[07] listwise deletion: {n_dropped} rows dropped "
            f"({n_dropped / before * 100:.4f}%) — any-null in {list(WEATHER_COLS)}",
            flush=True,
        )
    return df.reset_index(drop=True), n_dropped


def _find_zero_variance(df_sub: pd.DataFrame, candidate_cols: tuple[str, ...]) -> list[str]:
    """Return columns whose std is 0 (or NaN) inside the subset."""
    dropped = []
    for c in candidate_cols:
        s = df_sub[c].std()
        if not (s > 0 and math.isfinite(s)):
            dropped.append(c)
    return dropped


def _find_pairwise_collinear(
    df_sub: pd.DataFrame,
    candidate_cols: list[str],
    threshold: float = COLLINEARITY_THRESHOLD,
) -> list[str]:
    """Return one column per pair with |pearson corr| >= threshold.

    2C-C4 MAGI-AKAGI P2 (3/3 vote) fix. In prefectures with 1-2 snow days
    (Ehime, Okayama), corr(snowfall_cm, snow_depth_max_cm) = 1.0 exactly, and
    the univariate std check misses the resulting rank deficiency. This helper
    catches the near-perfect pair and drops the second column of each pair
    (deterministic ordering: keep the earlier column in candidate_cols).
    Only pairs whose correlation is finite are considered — a constant column
    would already have been removed by _find_zero_variance.
    """
    if len(candidate_cols) < 2:
        return []
    dropped: list[str] = []
    for i, a in enumerate(candidate_cols):
        if a in dropped:
            continue
        for b in candidate_cols[i + 1:]:
            if b in dropped:
                continue
            corr = df_sub[a].corr(df_sub[b])
            if corr is None or not math.isfinite(corr):
                continue
            if abs(corr) >= threshold:
                dropped.append(b)
    return dropped


def _find_dropped_covariates(
    df_sub: pd.DataFrame,
    candidate_cols: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    """Combined zero-variance + pairwise-collinearity check.

    Returns (all_dropped, drop_reasons_parallel) so JSON diagnostics can
    surface *why* each covariate was excluded (zero_variance vs collinear).
    """
    zero_var = _find_zero_variance(df_sub, candidate_cols)
    survivors = [c for c in candidate_cols if c not in zero_var]
    collinear = _find_pairwise_collinear(df_sub, survivors)
    all_dropped = list(zero_var) + list(collinear)
    reasons = (
        ["zero_variance"] * len(zero_var)
        + ["pairwise_collinear"] * len(collinear)
    )
    return all_dropped, reasons


def build_design_single(
    df_sub: pd.DataFrame,
    dropped_covariates: list[str],
) -> tuple[pd.DataFrame, pd.Series]:
    """exog = const + effective MAIN_EFFECTS + drop-first year/month/weekday dummies."""
    effective_effects = [c for c in BASE_MAIN_EFFECTS if c not in dropped_covariates]
    parts = [df_sub[effective_effects].astype(float)]
    for col in DUMMY_COLS:
        d = pd.get_dummies(df_sub[col], prefix=col, drop_first=True).astype(float)
        parts.append(d)
    X = pd.concat(parts, axis=1)
    X = sm.add_constant(X, has_constant="add")
    y = df_sub["total_count"].astype(float)
    return X, y


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def fit_single_prefecture(
    df_sub: pd.DataFrame,
    label: str,
) -> dict:
    """NB2 MLE + Poisson warm start + HC1 heteroscedasticity-robust SE.

    2C-C4 MAGI-AKAGI P1 fix: original design requested `cov_type='cluster'`
    with date as the grouping variable, but each date has exactly one row
    inside a single-prefecture subset, so the cluster sandwich reduces to HC0
    (with a 0.8% finite-sample scaling). HC1 is the correct label and applies
    the (N/(N-K)) small-sample correction preferred for regression inference.

    Returns a dict with `converged` flag and `non_conv_reason` string. On
    non-convergence coef/SE/ratio/CI/p and se_source are None (JSON-null) so
    the forest plot can annotate the row instead of the whole run failing.
    """
    dropped, drop_reasons = _find_dropped_covariates(df_sub, WEATHER_COLS)
    result: dict = {
        "prefecture_en": label,
        "n_obs": int(len(df_sub)),
        "dropped_covariates": dropped,
        "dropped_reason": drop_reasons,
        "converged": False,
        "non_conv_reason": None,
        "alpha_mle_nb2": None,
        "is_fri13_coef": None,
        "is_fri13_se": None,
        "is_fri13_p": None,
        "count_ratio": None,
        "count_ratio_ci_low": None,
        "count_ratio_ci_high": None,
        "se_source": None,
        "nb2_runtime_warnings": [],
    }

    try:
        X, y = build_design_single(df_sub, dropped)
    except Exception as exc:
        result["non_conv_reason"] = f"design build failed: {type(exc).__name__}: {exc}"
        return result

    # Poisson warm start
    try:
        poisson = sm.Poisson(y, X).fit(disp=False, maxiter=200)
    except Exception as exc:
        result["non_conv_reason"] = f"poisson raise: {type(exc).__name__}: {exc}"
        return result
    if not poisson.mle_retvals.get("converged", False):
        result["non_conv_reason"] = "poisson non-conv"
        return result
    start = np.concatenate([poisson.params.values, [1.0]])

    # NB2 MLE iid
    nb = NegativeBinomial(y, X, loglike_method="nb2")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        try:
            fit_iid = nb.fit(start_params=start, disp=False, maxiter=500)
        except Exception as exc:
            result["non_conv_reason"] = f"nb2 iid raise: {type(exc).__name__}: {exc}"
            return result
    result["nb2_runtime_warnings"] = sorted({
        str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)
    })
    if not fit_iid.mle_retvals.get("converged", False):
        result["non_conv_reason"] = "nb2 iid non-conv"
        return result

    # NB2 refit with HC1 heteroscedasticity-robust SE
    try:
        fit_c = nb.fit(
            start_params=fit_iid.params.values,
            cov_type="HC1",
            disp=False,
            maxiter=50,
        )
    except Exception as exc:
        result["non_conv_reason"] = f"nb2 HC1 raise: {type(exc).__name__}: {exc}"
        return result
    if not fit_c.mle_retvals.get("converged", False):
        result["non_conv_reason"] = "nb2 HC1 non-conv"
        return result

    # Extract is_fri13 from HC1 refit
    if "is_fri13" not in fit_c.params.index:
        result["non_conv_reason"] = "is_fri13 not in params (unexpected)"
        return result
    coef = _safe_float(fit_c.params["is_fri13"])
    se = _safe_float(fit_c.bse["is_fri13"])
    if coef is None or se is None or se <= 0:
        result["non_conv_reason"] = f"non-finite coef/SE: coef={coef}, se={se}"
        return result

    result.update({
        "converged": True,
        "alpha_mle_nb2": _safe_float(fit_iid.params["alpha"]),
        "is_fri13_coef": coef,
        "is_fri13_se": se,
        "is_fri13_p": _safe_float(fit_c.pvalues["is_fri13"]),
        "count_ratio": _safe_exp(coef),
        "count_ratio_ci_low": _safe_exp(coef - Z95 * se),
        "count_ratio_ci_high": _safe_exp(coef + Z95 * se),
        "se_source": "hc1_heteroscedasticity_robust",
    })
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_all_prefectures(df: pd.DataFrame) -> list[dict]:
    """Fit 47 prefectures in alphabetical order for deterministic output."""
    prefs = sorted(df["prefecture_en"].unique())
    print(f"[07] fitting {len(prefs)} prefectures...", flush=True)
    results = []
    for i, pref in enumerate(prefs, start=1):
        sub = df.loc[df["prefecture_en"] == pref].reset_index(drop=True)
        r = fit_single_prefecture(sub, pref)
        status = "OK" if r["converged"] else f"SKIP ({r['non_conv_reason']})"
        cr = r["count_ratio"]
        cr_str = f"{cr:.4f}" if cr is not None else "----"
        print(f"  [{i:2d}/{len(prefs)}] {pref:<12s} n={r['n_obs']} "
              f"dropped={r['dropped_covariates']} ratio={cr_str} {status}",
              flush=True)
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def _v(id_: str, value, label: str, section: str, fmt: str = ".2f") -> dict:
    return {"id": id_, "value": value, "label": label, "section": section, "format": fmt}


def _bh_fdr_significant(pvals: list[float], q: float = 0.05) -> int:
    """Count significant tests under Benjamini-Hochberg FDR control at level q.

    Standard step-up procedure: sort p-values ascending, find largest k with
    p_(k) <= (k/m) * q, declare tests 1..k significant.
    """
    if not pvals:
        return 0
    m = len(pvals)
    sorted_p = sorted(pvals)
    k_max = 0
    for k, p in enumerate(sorted_p, start=1):
        if p <= (k / m) * q:
            k_max = k
    return k_max


def build_truth_values(results: list[dict]) -> list[dict]:
    """Aggregate summary values for truth.json schema (per-prefecture entries
    are in `diagnostics.results` — truth values are counts, extrema, and
    multi-test disclosure fields to prevent selective reading in C5)."""
    v = []
    n_pref = len(results)
    n_conv = sum(1 for r in results if r["converged"])
    v.append(_v("pref_by_pref_n_prefectures", n_pref,
                "N prefectures fitted (Figure S3 forest)", "methods", "d"))
    v.append(_v("pref_by_pref_n_converged", n_conv,
                "N prefectures converged (Figure S3 forest)", "methods", "d"))
    v.append(_v("pref_by_pref_n_non_converged", n_pref - n_conv,
                "N prefectures non-converged (Figure S3 forest)", "methods", "d"))

    conv = [r for r in results if r["converged"]]
    if conv:
        ratios = [r["count_ratio"] for r in conv]
        max_r = max(conv, key=lambda r: r["count_ratio"])
        min_r = min(conv, key=lambda r: r["count_ratio"])
        v.append(_v("pref_by_pref_ratio_max_pref", max_r["prefecture_en"],
                    "Prefecture with maximum is_fri13 count ratio", "results", "s"))
        v.append(_v("pref_by_pref_ratio_max", max_r["count_ratio"],
                    "Max prefecture-level is_fri13 count ratio", "results", ".2f"))
        v.append(_v("pref_by_pref_ratio_min_pref", min_r["prefecture_en"],
                    "Prefecture with minimum is_fri13 count ratio", "results", "s"))
        v.append(_v("pref_by_pref_ratio_min", min_r["count_ratio"],
                    "Min prefecture-level is_fri13 count ratio", "results", ".2f"))
        v.append(_v("pref_by_pref_ratio_median", float(np.median(ratios)),
                    "Median prefecture-level is_fri13 count ratio", "results", ".2f"))

        # Multiple-testing disclosure (2C-C4 MAGI-AKAGI P2 + AKAGI B4).
        # Prevents C5 selective reading of "5 prefectures significant" without
        # the binomial-null and multiplicity-correction context.
        n_ci_excludes_one = sum(
            1 for r in conv
            if r["count_ratio_ci_low"] is not None
            and r["count_ratio_ci_high"] is not None
            and (r["count_ratio_ci_low"] > 1.0 or r["count_ratio_ci_high"] < 1.0)
        )
        v.append(_v("pref_by_pref_n_ci_excludes_one", n_ci_excludes_one,
                    "N prefectures whose 95% CI excludes 1.0 (nominal alpha=0.05, uncorrected)",
                    "results", "d"))

        # Binomial null: under global null all 45 marginal tests are
        # independent Bernoulli(alpha=0.05). Report one-sided greater p.
        binom_p = float(scipy_stats.binomtest(
            n_ci_excludes_one, n=n_conv, p=0.05, alternative="greater"
        ).pvalue)
        v.append(_v("pref_by_pref_n_ci_excludes_one_binomial_p", binom_p,
                    "Binomial one-sided p-value: excess significant prefectures vs alpha=0.05 null",
                    "results", ".3f"))

        pvals = [r["is_fri13_p"] for r in conv if r["is_fri13_p"] is not None]
        bonferroni_alpha = 0.05 / max(1, len(pvals))
        n_bonf = sum(1 for p in pvals if p <= bonferroni_alpha)
        v.append(_v("pref_by_pref_n_bonferroni_significant", n_bonf,
                    "N prefectures significant under Bonferroni correction (alpha_family=0.05)",
                    "results", "d"))

        n_bh = _bh_fdr_significant(pvals, q=0.05)
        v.append(_v("pref_by_pref_n_bh_fdr_significant", n_bh,
                    "N prefectures significant under Benjamini-Hochberg FDR (q=0.05)",
                    "results", "d"))
    return v


def write_results(
    results: list[dict],
    out_path: Path,
    n_listwise_dropped: int = 0,
) -> None:
    """Persist prefecture-level results to JSON.

    dropped_map surfaces WHY each covariate was excluded (zero_variance vs
    pairwise_collinear) so the manuscript / referee response can trace the
    Ehime-Okayama recovery back to the collinearity check.
    """
    dropped_map = {
        r["prefecture_en"]: [
            {"col": c, "reason": reason}
            for c, reason in zip(r["dropped_covariates"], r["dropped_reason"])
        ]
        for r in results
        if r["dropped_covariates"]
    }
    n_conv = sum(1 for r in results if r["converged"])
    doc = {
        "project": "friday13th",
        "phase": "2C-C4",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "script": "src/07_prefecture_by_prefecture_fit.py",
        "model_notes": (
            "Per-prefecture NB2 MLE reusing the mean model from 2C-C2-e "
            "primary (weather+holiday+cloud with year/month/weekday FE); "
            "prefecture FE dropped since each subset is a single prefecture. "
            "Standard errors are HC1 heteroscedasticity-robust (Cameron & "
            "Miller 2015 §3.4): within a single-prefecture subset each date "
            "has exactly one observation, so cluster-on-date is identified "
            "as HC0 with a ~0.8% finite-sample scaling — HC1 is reported "
            "instead as the honest label. Weather covariates are dropped "
            "per prefecture when zero-variance (6 prefectures — Kagawa/"
            "Miyazaki/Oita/Okinawa/Osaka/Shizuoka) or pairwise-collinear "
            "(|corr| >= 0.999; snowfall_cm vs snow_depth_max_cm in 2 "
            "prefectures with 1-2 snow days). Non-convergence is a flag, "
            "not a raise. See src/03_prefecture_panel_weather_nb.py for the "
            "panel-model counterpart with two-way cluster (prefecture, date) SE."
        ),
        "values": build_truth_values(results),
        "diagnostics": {
            "n_prefectures": len(results),
            "n_converged": n_conv,
            "n_non_converged": len(results) - n_conv,
            "n_listwise_dropped": n_listwise_dropped,
            "dropped_covariates_by_prefecture": dropped_map,
            "results": results,
        },
    }
    out_path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )


def main() -> None:
    print(f"[07] loading prefecture panel from {PREF_ACC}", flush=True)
    df, n_listwise_dropped = load_prefecture_panel()
    print(f"[07] loaded rows={len(df):,} prefectures={df['prefecture_en'].nunique()} "
          f"listwise_dropped={n_listwise_dropped}",
          flush=True)
    results = run_all_prefectures(df)
    write_results(results, OUT_JSON, n_listwise_dropped=n_listwise_dropped)
    n_conv = sum(1 for r in results if r["converged"])
    print(f"\n[07] wrote {OUT_JSON}", flush=True)
    print(f"[07] {n_conv}/{len(results)} prefectures converged", flush=True)


if __name__ == "__main__":
    main()
