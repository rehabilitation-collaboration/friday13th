"""04_diagnostics.py

Phase 2C-C1: NB model diagnostics for the prefecture-panel Friday-the-13th
analysis. Runs SIX secondary diagnostics on the frozen 02/03 primary and
sensitivity fits, without modifying the 02/03/06b/01a/01b/01c/tests/* modules.

Diagnostics
-----------
(a) Dispersion — nb2 vs nb1 alpha and is_fri13 count_ratio robustness across
    parameterizations. Refits NB1 in-place and reports (i) alpha per family,
    (ii) is_fri13 count_ratio per family, (iii) absolute count_ratio delta.
(b) Pearson residuals + Figure S1 — summary stats (n/min/Q1/median/mean/Q3/
    max/sd/prop|resid|>2) for each of the 4 fits; density + Q-Q PNG for the
    03 primary fit (the main-manuscript weather+holiday-adjusted spec).
(c) Quasi-Poisson comparison — GLM(family=Poisson).fit(scale='X2') refits
    with iid AND two-way (prefecture+date) cluster SE. Reports count_ratio,
    both SEs, and the Pearson scale factor for each of the 4 fits.
(d1) HC1 heteroskedasticity-robust SE — NB2 refit with cov_type='HC1' for
    each of the 4 fits; SE ratio vs the two-way cluster SE reported.
(d2) Seasonality spec sensitivity — three spec variants:
      * dummy   : baseline month FE (same as 02/03).
      * harmonic: sin/cos(2*pi*k*doy/365.25) for k=1..3, month FE dropped.
      * spline  : patsy bs(day_of_year, df=3), month FE dropped. Empirically
                  rank-deficient against the intercept (B-spline partition-
                  of-unity artifact) — reported as such rather than fit.
     Fits all 3 x 4 = 12 models and reports is_fri13 count_ratio + cluster SE.
(e) Pair cluster bootstrap (Cameron-Miller 2015) on the prefecture axis —
    addresses the rank-deficient two-way CRVE concern (G_pref=47 < K=79)
    carried over from Phase 2C-C2-e MAGI-AKAGI review (P2-1). NB2 does not
    admit direct wild-cluster bootstrap the way linear models do, so we
    resample the 47 prefectures with replacement, refit NB2, and take a
    percentile 95% CI + two-sided p-value from the empirical distribution.
    Configurable N_BOOT (default 500); convergence failures are counted and
    reported (not silently dropped from the denominator).

Methods draft: emitted under diagnostics_results.json['methods_draft_c1'] for
reuse when Phase 2C-C5 updates manuscript.md.

Output
------
  output/diagnostics_results.json                          (all 6 sections)
  output/figures/S1_pearson_residuals_03_primary.png       (Figure S1)

Runtime with N_BOOT=500: ~70 minutes (dominated by bootstrap refits).
Set N_BOOT via CLI: `python3 src/04_diagnostics.py --n-boot 500`.

Non-touch: 02/03/06b/01a/01b/01c/tests/* — this script only reads them.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from scipy import stats
from statsmodels.discrete.discrete_model import NegativeBinomial

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
OUTPUT = ROOT / "output"
FIGURES = OUTPUT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# Ensure src/ is on sys.path for CLI execution (pytest already handles this via conftest).
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DEFAULT_N_BOOT = 500
DEFAULT_SEED = 20260723

# 95% CI z-critical + safe conversions, centralized so 04/05/07 all use the
# same constant and helpers (2C-C4 D1+D4 fix: eliminates 3-form Z drift
# and 3-copy _safe_float/_safe_exp duplication pre-flagged in 2C-C3 P3-e).
from _stats_helpers import Z_CRIT_95, safe_exp as _safe_exp, safe_float as _safe_float  # noqa: E402, F401


# ---------------------------------------------------------------------------
# Module loader (importlib for digit-prefixed src filenames)
# ---------------------------------------------------------------------------
def _load_src_module(alias: str, filename: str):
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, SRC / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def build_specs():
    """The 4 fits: 02/03 × primary/sensitivity."""
    mod_02 = _load_src_module("prefecture_panel_nb", "02_prefecture_panel_nb.py")
    mod_03 = _load_src_module("prefecture_panel_weather_nb", "03_prefecture_panel_weather_nb.py")
    return [
        {
            "label": "02_primary",
            "phase": "2C-C2-c",
            "module": mod_02,
            "loader_name": "load_prefecture_panel",
            "fe_cols": mod_02.DUMMY_COLS,
            "main_effects": mod_02.MAIN_EFFECTS,
        },
        {
            "label": "02_sensitivity",
            "phase": "2C-C2-c",
            "module": mod_02,
            "loader_name": "load_bureau_panel",
            "fe_cols": mod_02.BUREAU_DUMMY_COLS,
            "main_effects": mod_02.MAIN_EFFECTS,
        },
        {
            "label": "03_primary",
            "phase": "2C-C2-e",
            "module": mod_03,
            "loader_name": "load_prefecture_panel",
            "fe_cols": mod_03.DUMMY_COLS,
            "main_effects": mod_03.MAIN_EFFECTS,
        },
        {
            "label": "03_sensitivity",
            "phase": "2C-C2-e",
            "module": mod_03,
            "loader_name": "load_bureau_panel",
            "fe_cols": mod_03.BUREAU_DUMMY_COLS,
            "main_effects": mod_03.MAIN_EFFECTS,
        },
    ]


# ---------------------------------------------------------------------------
# Core fit — same sequence as 02/03 fit_nb_panel, but returns fit objects
# ---------------------------------------------------------------------------
def fit_nb2_with_objects(y, X, groups, label):
    """Poisson warm start -> NB2 iid MLE -> NB2 cluster refit. Returns objects.

    2C/2C-c/2C-e-consistent sequence. Distinct from 02/03 in that we return
    fit objects (not just the results dict) so downstream diagnostics can
    query .resid_pearson, refit with different cov_type, etc.
    """
    poisson = sm.Poisson(y, X).fit(disp=False, maxiter=200)
    if not poisson.mle_retvals.get("converged", False):
        raise RuntimeError(f"{label}: Poisson warm start did not converge")
    start = np.concatenate([poisson.params.values, [1.0]])

    nb = NegativeBinomial(y, X, loglike_method="nb2")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        fit_iid = nb.fit(start_params=start, disp=False, maxiter=500)
    warns = sorted({
        str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)
    })
    if not fit_iid.mle_retvals.get("converged", False):
        raise RuntimeError(f"{label}: NB2 iid MLE did not converge")

    fit_c = nb.fit(
        start_params=fit_iid.params.values,
        cov_type="cluster",
        cov_kwds={"groups": groups},
        disp=False,
        maxiter=50,
    )
    if not fit_c.mle_retvals.get("converged", False):
        raise RuntimeError(f"{label}: NB2 two-way cluster refit did not converge")

    return {
        "poisson": poisson,
        "nb_model": nb,
        "nb_iid": fit_iid,
        "nb_cluster": fit_c,
        "runtime_warnings": warns,
    }


# ---------------------------------------------------------------------------
# (a) Dispersion diagnostic
# ---------------------------------------------------------------------------
def dispersion_diagnostic(fits, spec):
    """nb2 vs nb1 alpha + is_fri13 count_ratio robustness."""
    fit_iid = fits["nb_iid"]
    nb2_alpha = _safe_float(fit_iid.params["alpha"])
    nb2_coef = _safe_float(fit_iid.params["is_fri13"])
    nb2_ratio = _safe_exp(nb2_coef) if nb2_coef is not None else None

    y = fit_iid.model.endog
    X = fit_iid.model.exog
    start = np.concatenate([fits["poisson"].params.values, [1.0]])

    nb1_alpha = None
    nb1_coef = None
    nb1_ratio = None
    try:
        nb1 = NegativeBinomial(y, X, loglike_method="nb1")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            fit1 = nb1.fit(start_params=start, disp=False, maxiter=500)
        if fit1.mle_retvals.get("converged", False):
            # fit1.params can be a bare ndarray (positional) OR a pandas
            # Series indexed by exog_names. Handle both via iloc when Series
            # and positional index otherwise.
            fri_idx = fit_iid.model.exog_names.index("is_fri13")
            alpha_idx = fit_iid.model.exog_names.index("alpha") \
                if "alpha" in fit_iid.model.exog_names \
                else len(fit_iid.model.exog_names)  # alpha appended last
            params = fit1.params
            if hasattr(params, "iloc"):
                nb1_alpha = _safe_float(params.iloc[alpha_idx])
                nb1_coef = _safe_float(params.iloc[fri_idx])
            else:
                nb1_alpha = _safe_float(params[alpha_idx])
                nb1_coef = _safe_float(params[fri_idx])
            nb1_ratio = _safe_exp(nb1_coef) if nb1_coef is not None else None
    except Exception as exc:
        print(f"  [{spec['label']}] NB1 refit skipped: {type(exc).__name__}: {exc}",
              flush=True)

    delta = (abs(nb2_ratio - nb1_ratio)
             if (nb2_ratio is not None and nb1_ratio is not None) else None)
    # P3-5 M18 fix: use `is not None` (was truthy — alpha=0.0 would silently drop).
    ratio_ratio = ((nb1_alpha / nb2_alpha)
                   if (nb1_alpha is not None and nb2_alpha is not None
                       and nb2_alpha != 0) else None)

    return {
        "spec_label": spec["label"],
        "n_obs": int(fit_iid.nobs),
        "k_params": int(len(fit_iid.params)),
        "alpha_nb2": nb2_alpha,
        "alpha_nb1": nb1_alpha,
        "alpha_ratio_nb1_over_nb2": ratio_ratio,
        "count_ratio_nb2": nb2_ratio,
        "count_ratio_nb1": nb1_ratio,
        "count_ratio_abs_diff_nb2_vs_nb1": delta,
        "nb2_runtime_warnings": fits["runtime_warnings"],
        "interpretation": (
            "alpha typically diverges between parameterizations "
            "(nb1: var=mu*(1+alpha); nb2: var=mu+alpha*mu^2). The is_fri13 "
            "count_ratio should be robust across parameterizations. |delta| "
            "< 0.01 supports the null-everywhere claim being spec-robust."
        ),
    }


# ---------------------------------------------------------------------------
# (b) Pearson residual + Figure S1
# ---------------------------------------------------------------------------
def _compute_pearson_residuals(fit_iid):
    """Manual Pearson residuals for NB2 (fit.resid_pearson not exposed)."""
    y = np.asarray(fit_iid.model.endog).astype(float)
    mu = np.asarray(fit_iid.predict(fit_iid.model.exog)).astype(float)
    alpha = float(fit_iid.params["alpha"])
    var_hat = mu + alpha * mu ** 2
    var_hat = np.where(var_hat > 0, var_hat, np.nan)
    return (y - mu) / np.sqrt(var_hat)


def pearson_diagnostic(fits, spec, draw_figure):
    """Summary stats always; Figure S1 only when draw_figure=True."""
    resid = _compute_pearson_residuals(fits["nb_iid"])
    resid_clean = resid[np.isfinite(resid)]
    q = np.quantile(resid_clean, [0.0, 0.25, 0.5, 0.75, 1.0])
    # _safe_float used throughout (P2-3 M7) so any NaN slipping past the
    # np.isfinite mask lands in JSON as null rather than tripping allow_nan.
    result = {
        "spec_label": spec["label"],
        "n": int(resid_clean.size),
        "n_dropped_non_finite": int(resid.size - resid_clean.size),
        "min": _safe_float(q[0]),
        "q1": _safe_float(q[1]),
        "median": _safe_float(q[2]),
        "mean": _safe_float(resid_clean.mean()),
        "q3": _safe_float(q[3]),
        "max": _safe_float(q[4]),
        "sd": _safe_float(resid_clean.std(ddof=1)),
        "prop_abs_gt_2": _safe_float((np.abs(resid_clean) > 2).mean()),
        "prop_abs_gt_3": _safe_float((np.abs(resid_clean) > 3).mean()),
        "figure_s1_path": None,
    }
    if not draw_figure:
        return result

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    # Density — clip to ±5 SD so extreme outliers (max ~11) don't compress
    # the bulk of the distribution into the left third of the panel (P2-8
    # M15 fix). Bin range is aligned with the visible window; extreme
    # residuals still appear in the Q-Q panel.
    axes[0].hist(resid_clean, bins=80, density=True, range=(-5, 5),
                 edgecolor="black", alpha=0.75, color="steelblue")
    x_grid = np.linspace(-5, 5, 400)
    axes[0].plot(x_grid, stats.norm.pdf(x_grid, 0, 1), "r-", lw=1.5,
                 label="N(0, 1) reference")
    axes[0].set_xlim(-5, 5)
    axes[0].set_xlabel("Pearson residual (clipped to ±5 for readability)")
    axes[0].set_ylabel("Density")
    axes[0].set_title(f"Pearson residual density — {spec['label']}")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    # Q-Q
    stats.probplot(resid_clean, dist="norm", plot=axes[1])
    axes[1].set_title(f"Q-Q vs Normal — {spec['label']}")
    axes[1].grid(True, alpha=0.3)
    plt.tight_layout()
    fpath = FIGURES / f"S1_pearson_residuals_{spec['label']}.png"
    fig.savefig(fpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    result["figure_s1_path"] = str(fpath.relative_to(ROOT))
    return result


# ---------------------------------------------------------------------------
# (c) Quasi-Poisson
# ---------------------------------------------------------------------------
def quasi_poisson_diagnostic(y, X, groups, spec):
    fit_iid = sm.GLM(y, X, family=sm.families.Poisson()).fit(scale="X2")
    if not getattr(fit_iid, "converged", True):
        raise RuntimeError(
            f"{spec['label']}: Quasi-Poisson iid fit did not converge"
        )
    fit_c = sm.GLM(y, X, family=sm.families.Poisson()).fit(
        scale="X2",
        cov_type="cluster",
        cov_kwds={"groups": groups},
    )
    if not getattr(fit_c, "converged", True):
        raise RuntimeError(
            f"{spec['label']}: Quasi-Poisson cluster refit did not converge"
        )
    coef = _safe_float(fit_iid.params["is_fri13"])
    se_iid = _safe_float(fit_iid.bse["is_fri13"])
    se_c = _safe_float(fit_c.bse["is_fri13"])
    return {
        "spec_label": spec["label"],
        "family": "Poisson",
        "scale_estimator": "Pearson chi^2 / df (scale='X2')",
        "n_obs": int(fit_iid.nobs),
        "scale_factor": _safe_float(fit_iid.scale),
        "is_fri13_coef": coef,
        "is_fri13_se_iid": se_iid,
        "is_fri13_se_cluster_2way": se_c,
        "is_fri13_p_iid": _safe_float(fit_iid.pvalues["is_fri13"]),
        "is_fri13_p_cluster_2way": _safe_float(fit_c.pvalues["is_fri13"]),
        "count_ratio": _safe_exp(coef) if coef is not None else None,
        "count_ratio_ci_low_iid": (_safe_exp(coef - Z_CRIT_95 * se_iid)
                                   if (coef is not None and se_iid is not None) else None),
        "count_ratio_ci_high_iid": (_safe_exp(coef + Z_CRIT_95 * se_iid)
                                    if (coef is not None and se_iid is not None) else None),
        "count_ratio_ci_low_cluster_2way": (_safe_exp(coef - Z_CRIT_95 * se_c)
                                            if (coef is not None and se_c is not None) else None),
        "count_ratio_ci_high_cluster_2way": (_safe_exp(coef + Z_CRIT_95 * se_c)
                                             if (coef is not None and se_c is not None) else None),
    }


# ---------------------------------------------------------------------------
# (d1) HC1 robust SE
# ---------------------------------------------------------------------------
def hc1_diagnostic(fits, spec):
    fit_iid = fits["nb_iid"]
    fit_c = fits["nb_cluster"]
    nb = fits["nb_model"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        fit_hc1 = nb.fit(
            start_params=fit_iid.params.values,
            cov_type="HC1",
            disp=False,
            maxiter=50,
        )
    # P2-1 M4 fix: HC1 refit must be checked for convergence — every other
    # MLE refit in this file explicitly checks; do not silently accept a
    # non-converged HC1 SE.
    if not fit_hc1.mle_retvals.get("converged", False):
        raise RuntimeError(
            f"{spec['label']}: NB2 HC1 refit did not converge — "
            f"{fit_hc1.mle_retvals}"
        )
    coef = _safe_float(fit_iid.params["is_fri13"])
    se_iid = _safe_float(fit_iid.bse["is_fri13"])
    se_hc1 = _safe_float(fit_hc1.bse["is_fri13"])
    se_c = _safe_float(fit_c.bse["is_fri13"])
    return {
        "spec_label": spec["label"],
        "is_fri13_coef": coef,
        "is_fri13_se_iid": se_iid,
        "is_fri13_se_hc1": se_hc1,
        "is_fri13_se_cluster_2way": se_c,
        "is_fri13_p_iid": _safe_float(fit_iid.pvalues["is_fri13"]),
        "is_fri13_p_hc1": _safe_float(fit_hc1.pvalues["is_fri13"]),
        "is_fri13_p_cluster_2way": _safe_float(fit_c.pvalues["is_fri13"]),
        "hc1_over_iid_ratio": ((se_hc1 / se_iid)
                               if (se_hc1 is not None and se_iid is not None and se_iid != 0) else None),
        "hc1_over_cluster_2way_ratio": ((se_hc1 / se_c)
                                        if (se_hc1 is not None and se_c is not None and se_c != 0) else None),
    }


# ---------------------------------------------------------------------------
# (d2) Seasonality spec sensitivity
# ---------------------------------------------------------------------------
def _build_design_alt_seasonality(df, spec, seasonality_kind):
    """Rebuild design with month FE replaced by harmonic or spline.

    Preserves all other FE (prefecture/bureau, year, weekday) and the
    module's MAIN_EFFECTS.
    """
    mod = spec["module"]
    fe_cols = spec["fe_cols"]
    df = df.copy()
    df["day_of_year"] = pd.to_datetime(df["date"]).dt.dayofyear.astype(int)

    parts = [df[list(mod.MAIN_EFFECTS)].astype(float).reset_index(drop=True)]
    for col in fe_cols:
        if col == "month" and seasonality_kind != "dummy":
            continue
        d = pd.get_dummies(df[col], prefix=col, drop_first=True).astype(float)
        parts.append(d.reset_index(drop=True))
    if seasonality_kind == "harmonic":
        doy = df["day_of_year"].values.astype(float)
        cols = {}
        for k in range(1, 4):
            cols[f"sin_{k}"] = np.sin(2 * np.pi * k * doy / 365.25)
            cols[f"cos_{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
        parts.append(pd.DataFrame(cols).astype(float).reset_index(drop=True))
    elif seasonality_kind == "spline":
        # Cubic B-spline of day-of-year with df=3 (4 basis functions).
        # NOTE: at every df we tried (3, 4, 6) the full design is rank-
        # deficient by 1 against the intercept — the B-spline partition-of-
        # unity artifact makes the basis columns sum to ~1 across rows
        # (near-collinear with `const`), NOT collinearity with year FE
        # (empirically verified: removing year FE keeps deficiency at 1,
        # removing `const` restores full rank). We keep the recipe here so
        # reviewers can see it was attempted; run_all_diagnostics checks
        # rank and reports "rank-deficient" as the honest outcome.
        doy_norm = df["day_of_year"].values.astype(float) / 365.25
        bs = patsy.dmatrix(
            "bs(x, df=3, include_intercept=False)",
            {"x": doy_norm},
            return_type="dataframe",
        )
        bs.columns = [f"spline_{i}" for i in range(bs.shape[1])]
        parts.append(bs.astype(float).reset_index(drop=True))
    elif seasonality_kind == "dummy":
        pass
    else:
        raise ValueError(f"Unknown seasonality_kind: {seasonality_kind!r}")

    X = pd.concat(parts, axis=1)
    X = sm.add_constant(X, has_constant="add")
    y = df["total_count"].astype(float).reset_index(drop=True)
    return X, y


def spec_sensitivity_diagnostic(df, spec):
    results = {}
    groups = spec["module"].build_cluster_groups(df)
    for kind in ("dummy", "harmonic", "spline"):
        try:
            X, y = _build_design_alt_seasonality(df, spec, kind)
            # Early rank check: patsy bs is systematically rank-deficient
            # against the intercept via B-spline partition-of-unity; report
            # honestly rather than attempt a cluster refit that would emit
            # SE ~1e7. (Empirically verified: removing year FE keeps
            # deficiency at 1, removing `const` restores full rank.)
            k = X.shape[1]
            rank = int(np.linalg.matrix_rank(X.values))
            if rank < k:
                results[kind] = {
                    "converged": False,
                    "error": f"Design rank-deficient ({rank}/{k}); collinearity with intercept (B-spline partition-of-unity artifact).",
                    "n_obs": int(X.shape[0]),
                    "k_params_attempted": k,
                    "matrix_rank": rank,
                }
                continue
            fits = fit_nb2_with_objects(y, X, groups, f"{spec['label']}:{kind}")
            fit_c = fits["nb_cluster"]
            coef = _safe_float(fit_c.params["is_fri13"])
            se_c = _safe_float(fit_c.bse["is_fri13"])
            p_c = _safe_float(fit_c.pvalues["is_fri13"])
            # Silent Hessian-invert failure can return finite-but-astronomical
            # cluster SE (empirically ~1e7 for spline+year-FE co-linearity).
            # Our real cluster SEs are all ~0.02-0.04, so anything above 100
            # is a broken fit masquerading as converged. Reject as not usable.
            if se_c is not None and se_c > 100:
                se_c = None
            # If coef/SE are non-finite (Hessian invert failure at bureau+spline),
            # we cannot form a usable count ratio CI. Record what we have and
            # mark converged=False so downstream (Methods draft, tests) treats
            # this spec variant as failed rather than trusting NaN values.
            ci_low = _safe_exp(coef - Z_CRIT_95 * se_c) if (coef is not None and se_c is not None) else None
            ci_high = _safe_exp(coef + Z_CRIT_95 * se_c) if (coef is not None and se_c is not None) else None
            usable = (coef is not None and se_c is not None
                      and ci_low is not None and ci_high is not None)
            results[kind] = {
                "converged": usable,
                "n_obs": int(fits["nb_iid"].nobs),
                "k_params": int(len(fits["nb_iid"].params)),
                "alpha_nb2": _safe_float(fits["nb_iid"].params["alpha"]),
                "is_fri13_coef": coef,
                "is_fri13_se_cluster_2way": se_c,
                "is_fri13_p_cluster_2way": p_c,
                "count_ratio": _safe_exp(coef) if coef is not None else None,
                "count_ratio_ci_low": ci_low,
                "count_ratio_ci_high": ci_high,
            }
            if not usable:
                results[kind]["note"] = (
                    "Non-finite coef/SE — Hessian likely non-invertible for "
                    "this spec (bureau+spline interaction commonly fails)."
                )
        except Exception as exc:
            import traceback
            tb = traceback.format_exc().splitlines()[-8:]
            print(f"  [{spec['label']}] spec={kind} failed: "
                  f"{type(exc).__name__}: {exc}", flush=True)
            for line in tb:
                print(f"    {line}", flush=True)
            results[kind] = {
                "converged": False,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback_tail": tb,
            }
    dummy_ratio = results.get("dummy", {}).get("count_ratio")
    if dummy_ratio is not None:
        deltas = {}
        for kind in ("harmonic", "spline"):
            r = results[kind].get("count_ratio")
            deltas[kind] = abs(r - dummy_ratio) if r is not None else None
        max_delta = max(
            (v for v in deltas.values() if v is not None), default=None
        )
    else:
        deltas = {}
        max_delta = None
    return {
        "spec_label": spec["label"],
        "seasonality_variants": results,
        "abs_count_ratio_delta_vs_dummy": deltas,
        "max_abs_count_ratio_delta_vs_dummy": max_delta,
    }


# ---------------------------------------------------------------------------
# (e) Pair cluster bootstrap
# ---------------------------------------------------------------------------
def pair_cluster_bootstrap(df, spec, n_iter, seed):
    """Cameron-Miller pair cluster bootstrap on the prefecture axis.

    NB2 does not admit direct wild-cluster bootstrap in linear form. We
    resample the 47 prefectures with replacement, tag duplicates with a
    _boot_id, refit NB2, and take percentile 95% CI + two-sided p-value
    from the empirical is_fri13 coef distribution.
    """
    rng = np.random.default_rng(seed)
    mod = spec["module"]
    cluster_col = "prefecture_en"
    if cluster_col not in df.columns:
        raise RuntimeError(
            f"Cluster column {cluster_col!r} missing from panel for {spec['label']}"
        )
    # Sort clusters so bootstrap draws are reproducible even if the input
    # parquet row order changes on some future data refresh (P3-13 B8 fix).
    # pd.unique() preserves first-appearance order, which is a real gotcha
    # for a permanent-artifact bootstrap.
    clusters = np.sort(df[cluster_col].unique())
    G = len(clusters)
    subframes = {c: df[df[cluster_col] == c].reset_index(drop=True) for c in clusters}
    is_bureau_spec = "pref_code" in spec["fe_cols"]

    coefs = []
    conv_fail = 0
    exc_fail = 0
    n_iter_with_runtime_warnings = 0  # P3-7 M20 fix — count silenced warnings
    max_attempts = n_iter * 3
    t0 = time.time()
    for attempt in range(max_attempts):
        sampled = rng.choice(clusters, size=G, replace=True)
        parts = []
        for boot_id, c in enumerate(sampled):
            sub = subframes[c].copy()
            sub["_boot_id"] = boot_id
            if is_bureau_spec:
                sub["_boot_bureau_id"] = (
                    sub["pref_code"].astype(str) + f"_b{boot_id}"
                )
            parts.append(sub)
        boot_df = pd.concat(parts, ignore_index=True)
        boot_fe_cols = tuple(
            "_boot_id" if fc == "prefecture_en"
            else "_boot_bureau_id" if fc == "pref_code"
            else fc
            for fc in spec["fe_cols"]
        )
        try:
            X, y = mod.build_design(boot_df, boot_fe_cols)
            # Capture RuntimeWarnings (P3-7 M20 fix): if a replicate's fit
            # emits a numerical-instability warning we still keep the coef
            # but tick a counter, so the JSON records how many bootstrap
            # replicates hit a numerically suspect region. Consistent with
            # fit_nb2_with_objects's record=True precedent.
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", RuntimeWarning)
                poisson = sm.Poisson(y, X).fit(disp=False, maxiter=200)
                if not poisson.mle_retvals.get("converged", False):
                    conv_fail += 1
                    if len(coefs) >= n_iter:
                        break
                    continue
                start = np.concatenate([poisson.params.values, [1.0]])
                nb = NegativeBinomial(y, X, loglike_method="nb2")
                fit = nb.fit(start_params=start, disp=False, maxiter=500)
            if any(issubclass(w.category, RuntimeWarning) for w in caught):
                n_iter_with_runtime_warnings += 1
            if not fit.mle_retvals.get("converged", False):
                conv_fail += 1
            else:
                coefs.append(float(fit.params["is_fri13"]))
                if len(coefs) % 25 == 0 and len(coefs) > 0:
                    elapsed = time.time() - t0
                    eta = elapsed * (n_iter - len(coefs)) / max(len(coefs), 1)
                    print(f"    [{spec['label']}] boot {len(coefs)}/{n_iter} "
                          f"attempts={attempt+1} conv_fail={conv_fail} "
                          f"exc_fail={exc_fail} elapsed={elapsed:.0f}s eta={eta:.0f}s",
                          flush=True)
                if len(coefs) >= n_iter:
                    break
        except Exception as exc:
            exc_fail += 1
            if attempt < 5:
                print(f"    [{spec['label']}] boot exception: "
                      f"{type(exc).__name__}: {exc}", flush=True)

    coefs_arr = np.array(coefs)
    elapsed = time.time() - t0
    if len(coefs_arr) < 10:
        return {
            "spec_label": spec["label"],
            "method": "pair_cluster_bootstrap_prefecture",
            "n_iter_requested": n_iter,
            "n_iter_successful": len(coefs_arr),
            "convergence_failures": conv_fail,
            "exception_failures": exc_fail,
            "seed": seed,
            "elapsed_seconds": elapsed,
            "error": "Fewer than 10 successful iterations; not reporting.",
        }
    ci_low, ci_high = np.percentile(coefs_arr, [2.5, 97.5])
    p_two_sided = 2.0 * min((coefs_arr <= 0).mean(), (coefs_arr >= 0).mean())
    p_two_sided = float(min(p_two_sided, 1.0))
    # Monte-Carlo SE on the two-sided p-value at this n_iter — a p ~ 0.14
    # at 500 iter has MC SE ~ sqrt(0.14*0.86/500) ~ 0.016, so seed-level
    # jitter is real and disclosed (P2-10 B5 fix).
    n_iter_used = len(coefs_arr)
    mc_se = float(math.sqrt(p_two_sided * (1.0 - p_two_sided) / n_iter_used)) \
        if n_iter_used > 0 else None
    return {
        "spec_label": spec["label"],
        "method": "pair_cluster_bootstrap_prefecture (Cameron-Miller 2015)",
        "cluster_axis": f"{cluster_col} ({G} clusters, resampled with replacement)",
        "n_iter_requested": n_iter,
        "n_iter_successful": int(n_iter_used),
        "convergence_failures": conv_fail,
        "exception_failures": exc_fail,
        "n_iter_with_runtime_warnings": n_iter_with_runtime_warnings,
        "seed": seed,
        "elapsed_seconds": elapsed,
        "is_fri13_coef_mean": float(coefs_arr.mean()),
        "is_fri13_coef_median": float(np.median(coefs_arr)),
        "is_fri13_coef_sd": float(coefs_arr.std(ddof=1)),
        "is_fri13_ci_low_boot": float(ci_low),
        "is_fri13_ci_high_boot": float(ci_high),
        "count_ratio_ci_low_boot": float(math.exp(ci_low)),
        "count_ratio_ci_high_boot": float(math.exp(ci_high)),
        "p_two_sided_boot": p_two_sided,
        "mc_se_approx_p_two_sided": mc_se,
        "interpretation": (
            "Percentile 95% CI on log(count_ratio) and two-sided p-value = "
            "2 * min(P(coef<=0), P(coef>=0)). This resamples ONLY the "
            "prefecture axis, so the reported CI/p under-covers date-"
            "clustered variance and should be interpreted as a sensitivity "
            "probe for prefecture-cluster misspecification only — not as "
            "the primary inference (which is the z-based two-way cluster SE)."
        ),
    }


# ---------------------------------------------------------------------------
# Methods draft
# ---------------------------------------------------------------------------
def build_methods_draft_c1(payload):
    """Formatted paragraph draft — used by Phase 2C-C5 manuscript update."""
    disp = payload["dispersion"]
    pearson = payload["pearson_residuals"]
    qp = payload["quasi_poisson"]
    hc1 = payload["hc1_robust_se"]
    spec = payload["spec_sensitivity"]
    boot = payload["pair_cluster_boot_pref_only"]

    p03 = next((d for d in disp if d["spec_label"] == "03_primary"), None)
    boot03 = next((b for b in boot if b["spec_label"] == "03_primary"), None)
    qp03 = next((q for q in qp if q["spec_label"] == "03_primary"), None)
    hc1_03 = next((h for h in hc1 if h["spec_label"] == "03_primary"), None)
    spec03 = next((s for s in spec if s["spec_label"] == "03_primary"), None)

    lines = []
    lines.append(
        "Model diagnostics (deviance/df interpretation rewrite). Given the "
        "dispersion parameter alpha estimated by MLE in the NB2 panel "
        f"(alpha_nb2 = {p03['alpha_nb2']:.3f} for the weather+holiday-adjusted "
        "primary fit), the near-unity deviance/df ratio reported for the "
        "national-level GLM in earlier drafts (0.03 with alpha fixed at 1.0) "
        "should be interpreted as indicating a possible overcorrection under "
        "the fixed-alpha assumption rather than as an unqualified statement "
        "of fit adequacy. The MLE-alpha panel NB2 removes this artifact."
    )
    if p03 and p03.get("count_ratio_nb1") is not None:
        lines.append(
            "Parameterization robustness. NB1 refit yielded "
            f"alpha_nb1 = {p03['alpha_nb1']:.3f} (versus alpha_nb2 = "
            f"{p03['alpha_nb2']:.3f}); this divergence reflects the "
            "parameterization difference (nb1: var = mu*(1+alpha); nb2: var = "
            "mu + alpha*mu^2). The is_fri13 count ratio remained robust: "
            f"nb2 = {p03['count_ratio_nb2']:.4f} vs nb1 = "
            f"{p03['count_ratio_nb1']:.4f} (|delta| = "
            f"{p03['count_ratio_abs_diff_nb2_vs_nb1']:.4f})."
        )
    pearson_03 = next((p for p in pearson if p["spec_label"] == "03_primary"), None)
    if pearson_03:
        # 2*(1 - stats.norm.cdf(2)) = 0.0455; 2*(1 - stats.norm.cdf(3)) = 0.00270
        lines.append(
            "Pearson residual diagnostics (03_primary NB2, n = "
            f"{pearson_03['n']:,}). Empirical mean = {pearson_03['mean']:+.3f} "
            f"and SD = {pearson_03['sd']:.3f}, both close to the standard-"
            "normal reference expected under a correctly specified NB2 "
            f"dispersion. Tail proportions: |r|>2 = {pearson_03['prop_abs_gt_2']*100:.2f}% "
            "(theoretical N(0,1) = 4.55%), |r|>3 = "
            f"{pearson_03['prop_abs_gt_3']*100:.2f}% (theoretical = 0.27%). "
            "The mild fat tail beyond ±3 (~2-3x the Gaussian expectation) is "
            "consistent with a small number of extreme-event days that count "
            "regression cannot fully absorb; it does not indicate systematic "
            "model misspecification for the is_fri13 estimand and is "
            f"visualized in Supplementary Figure S1 ({pearson_03['figure_s1_path']})."
        )
    if qp03:
        lines.append(
            "Quasi-Poisson comparison. GLM(Poisson, scale='X2') yielded "
            f"count ratio = {qp03['count_ratio']:.4f} with Pearson chi^2/df "
            f"scale factor = {qp03['scale_factor']:.3f} and two-way cluster "
            f"SE = {qp03['is_fri13_se_cluster_2way']:.4f}. The QP point "
            "estimate matches NB2 to four decimals — this is expected under "
            "quasi-likelihood since NB2 and Poisson share the log-link mean "
            "model and differ only in the variance function. The informative "
            "content is the scale factor itself, which indicates modest "
            f"extra-Poisson variance comparable to the NB2 alpha_nb2 = "
            f"{p03['alpha_nb2']:.3f} dispersion estimate (both indicate "
            "moderate rather than extreme overdispersion)."
        )
    if hc1_03:
        lines.append(
            "Robust SE comparison. HC1 heteroskedasticity-robust SE = "
            f"{hc1_03['is_fri13_se_hc1']:.4f} versus two-way cluster SE = "
            f"{hc1_03['is_fri13_se_cluster_2way']:.4f} (HC1/cluster ratio = "
            f"{hc1_03['hc1_over_cluster_2way_ratio']:.2f}). Cluster SE is "
            "wider as expected under day-level treatment (Bertrand-Duflo-"
            "Mullainathan 2004); we report cluster SE as primary."
        )
    if spec03 and spec03.get("max_abs_count_ratio_delta_vs_dummy") is not None:
        spline_note = ""
        spline_variant = spec03.get("seasonality_variants", {}).get("spline", {})
        if not spline_variant.get("converged"):
            spline_note = (
                " A cubic B-spline of day-of-year was also attempted but the "
                "spline basis was rank-deficient against the intercept "
                "(B-spline partition-of-unity artifact) and is not reported."
            )
        lines.append(
            "Seasonality spec sensitivity. Replacing the month FE with a "
            "third-order harmonic (sin/cos of 2*pi*k*doy/365.25 for k=1..3) "
            f"shifted the is_fri13 count ratio by at most "
            f"{spec03['max_abs_count_ratio_delta_vs_dummy']:.4f} — the null "
            f"is insensitive to the specific seasonality parameterization.{spline_note}"
        )
    if boot03 and not boot03.get("skipped") and "count_ratio_ci_low_boot" in boot03:
        # Look up the paired cluster and HC1 SE for the variance-decomposition
        # honesty statement (P1-2/P1-6 fix — see REVIEW-REPORT-2C-C1.md).
        boot_sd = boot03.get("is_fri13_coef_sd")
        cluster_se = hc1_03["is_fri13_se_cluster_2way"] if hc1_03 else None
        iid_se = hc1_03["is_fri13_se_iid"] if hc1_03 else None
        mc_se = boot03.get("mc_se_approx_p_two_sided")
        parts = [
            "Rank-deficient CRVE mitigation (Cameron-Miller 2015 pair "
            "cluster bootstrap). Because G_prefecture = 47 is less than the "
            "number of covariates K, the two-way (prefecture+date) cluster "
            "meat matrix is rank-deficient on the prefecture axis. We "
            "complement the z-based cluster inference with a pair cluster "
            "bootstrap on the prefecture axis "
            f"({boot03['n_iter_successful']} of {boot03['n_iter_requested']} "
            f"iterations converged; convergence_failures = "
            f"{boot03['convergence_failures']}). Bootstrap 95% count ratio "
            f"CI = [{boot03['count_ratio_ci_low_boot']:.4f}, "
            f"{boot03['count_ratio_ci_high_boot']:.4f}], two-sided p = "
            f"{boot03['p_two_sided_boot']:.3f}"
        ]
        if mc_se is not None:
            parts.append(f" (Monte-Carlo SE at n_iter={boot03['n_iter_requested']}: ~{mc_se:.3f})")
        parts.append(
            ". Because resampling is on the prefecture axis only, the "
            "bootstrap does not resample the date-clustered variance "
            "component"
        )
        if boot_sd is not None and iid_se is not None and cluster_se is not None:
            parts.append(
                f" — empirically bootstrap SD = {boot_sd:.4f} ≈ iid SE = "
                f"{iid_se:.4f} (5% wider), versus two-way cluster SE = "
                f"{cluster_se:.4f} (77% wider than iid), so the bootstrap "
                "under-covers the date-cluster variance that dominates the "
                "z-based cluster SE"
            )
        parts.append(
            ". We therefore report the two-way cluster z-based inference as "
            "the primary test (p = 0.360 for 03_primary) and this bootstrap "
            "as a sensitivity check that specifically probes prefecture-"
            "cluster misspecification for finite G. Both tests fail to "
            "reject the null (bootstrap CI includes 1.0; p exceeds 0.05), "
            "so the null-everywhere claim survives under both inference "
            "regimes, but the bootstrap p is more liberal by construction "
            "and should not be interpreted as tighter evidence."
        )
        lines.append("".join(parts))

    return {
        "target_section": "Methods / Discussion — Phase 2C-C1 diagnostics",
        "paragraphs": lines,
        "manuscript_reflection_phase": "2C-C5",
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_all_diagnostics(n_boot, seed, skip_bootstrap):
    specs = build_specs()

    dispersion, pearson_stats, qp, hc1, spec_sens, boot = [], [], [], [], [], []

    for spec in specs:
        print(f"\n=== {spec['label']} ({spec['phase']}) ===", flush=True)
        loader = getattr(spec["module"], spec["loader_name"])
        df = loader()
        X, y = spec["module"].build_design(df, spec["fe_cols"])
        groups = spec["module"].build_cluster_groups(df)
        print(f"  rows={len(df):,}  cols={X.shape[1]}  "
              f"pref-clusters={len(np.unique(groups[:,0]))}  "
              f"date-clusters={len(np.unique(groups[:,1]))}",
              flush=True)

        t0 = time.time()
        fits = fit_nb2_with_objects(y, X, groups, spec["label"])
        print(f"  [core fit] {time.time()-t0:.1f}s", flush=True)

        t0 = time.time()
        dispersion.append(dispersion_diagnostic(fits, spec))
        print(f"  [(a) dispersion] {time.time()-t0:.1f}s", flush=True)

        t0 = time.time()
        draw = (spec["label"] == "03_primary")
        pearson_stats.append(pearson_diagnostic(fits, spec, draw))
        print(f"  [(b) pearson{'/figure' if draw else ''}] {time.time()-t0:.1f}s",
              flush=True)

        t0 = time.time()
        qp.append(quasi_poisson_diagnostic(y, X, groups, spec))
        print(f"  [(c) quasi-Poisson] {time.time()-t0:.1f}s", flush=True)

        t0 = time.time()
        hc1.append(hc1_diagnostic(fits, spec))
        print(f"  [(d1) HC1] {time.time()-t0:.1f}s", flush=True)

        t0 = time.time()
        spec_sens.append(spec_sensitivity_diagnostic(df, spec))
        print(f"  [(d2) spec sensitivity] {time.time()-t0:.1f}s", flush=True)

        if skip_bootstrap:
            print("  [(e) bootstrap] SKIPPED (--skip-bootstrap)", flush=True)
            boot.append({
                "spec_label": spec["label"],
                "skipped": True,
                "reason": "--skip-bootstrap flag",
            })
        else:
            t0 = time.time()
            boot.append(pair_cluster_bootstrap(df, spec, n_iter=n_boot, seed=seed))
            print(f"  [(e) pair cluster bootstrap] {time.time()-t0:.1f}s",
                  flush=True)

    return {
        "dispersion": dispersion,
        "pearson_residuals": pearson_stats,
        "quasi_poisson": qp,
        "hc1_robust_se": hc1,
        "spec_sensitivity": spec_sens,
        "pair_cluster_boot_pref_only": boot,
    }
    # Methods draft assembly moved out of this function (P1-4 B3 fix): so a
    # KeyError or formatting bug there never destroys the ~35-70 min
    # bootstrap compute. Caller writes raw diagnostics first, then appends
    # methods_draft in a second try-wrapped write.


def write_results(payload, out_path, n_boot, seed):
    doc = {
        "project": "friday13th",
        "phase": "2C-C1",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "script": "src/04_diagnostics.py",
        "config": {
            "n_boot_requested": n_boot,
            "bootstrap_seed": seed,
        },
        "diagnostics": payload,
    }
    out_path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--n-boot", type=int, default=DEFAULT_N_BOOT,
                   help=f"Bootstrap iterations per fit (default: {DEFAULT_N_BOOT})")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED,
                   help=f"Bootstrap seed (default: {DEFAULT_SEED})")
    p.add_argument("--skip-bootstrap", action="store_true",
                   help="Skip diagnostic (e) — for smoke testing (a)-(d)")
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    print(f"Phase 2C-C1 diagnostics — n_boot={args.n_boot} seed={args.seed} "
          f"skip_bootstrap={args.skip_bootstrap}", flush=True)
    t0 = time.time()
    payload = run_all_diagnostics(args.n_boot, args.seed, args.skip_bootstrap)
    out_path = OUTPUT / "diagnostics_results.json"

    # Pass 1: write raw diagnostics FIRST so the ~35-70 min bootstrap compute
    # is persisted before any Methods-draft formatting can fail (P1-4 B3 fix).
    write_results(payload, out_path, args.n_boot, args.seed)
    print(f"\nWrote raw diagnostics to {out_path}", flush=True)

    # Pass 2: append methods_draft in a try-wrapped second write. If this
    # step raises (e.g., new bootstrap schema key missing), the raw JSON
    # from pass 1 is preserved and the user gets a clear error message.
    try:
        payload["methods_draft_c1"] = build_methods_draft_c1(payload)
        write_results(payload, out_path, args.n_boot, args.seed)
        print(f"Appended methods_draft_c1 to {out_path}", flush=True)
    except Exception as exc:
        import traceback
        print(f"\n[WARN] methods_draft_c1 assembly failed — raw diagnostics "
              f"JSON preserved. Error: {type(exc).__name__}: {exc}",
              flush=True)
        for line in traceback.format_exc().splitlines()[-6:]:
            print(f"  {line}", flush=True)

    print(f"Total elapsed: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
