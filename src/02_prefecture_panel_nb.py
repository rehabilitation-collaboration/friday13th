"""02_prefecture_panel_nb.py

Phase 2C-C2-c / C2-c-sensitivity:
Prefecture- and bureau-level Negative Binomial panel regression with MLE alpha
and two-way cluster-robust SE (prefecture + date). Addresses GPT V1 Major 5
(weather endogeneity from accident-location weighting) via full reconstruction
on prefecture x day panel, and Major 4 (dispersion parameter suspicion) via
MLE alpha instead of the fixed alpha=1.0 in 02_main_analysis.py::adjusted_negbin().

Model
-----
  endog = total_count
  exog  = is_fri13 + is_13th + cloud_cover
          + prefecture FE + year FE + month FE + weekday FE
  loglike_method = 'nb2' (variance = mu + alpha * mu^2)
  Poisson warm start; alpha estimated by MLE.

  is_13th main effect is included so the is_fri13 coefficient captures the
  Friday-the-13th-specific increment beyond any generic 13th-of-month effect.

Cluster-robust SE (two-way: prefecture + date)
----------------------------------------------
  Both primary and sensitivity use two-way clustering on (prefecture_en, date).
  is_fri13 is a date-level treatment (identical across all prefectures on any
  given day), so single-way prefecture clustering understates SE by ignoring
  cross-prefecture within-date correlation (Bertrand-Duflo-Mullainathan 2004).
  Sensitivity clusters by prefecture_en (not pref_code) even though its FE is
  at bureau level, so Hokkaido's 5 police bureaus are treated as one cluster
  (conservative for any Hokkaido-wide non-weather shock).

Design decisions (see PLAN-gpt-review-cycle.md Phase 2C C2-c and handoff):
  * MLE alpha (not alpha=1.0 fixed).
  * All-days model (not Friday-only): identification is clearer and weekday
    confounding is absorbed by weekday FE.
  * is_holiday and is_obon are NOT yet in the panel — the panel parquet itself
    lacks these columns and would need regeneration from the upstream NPA
    source (fullmoon-accident/data/processed/accidents_clean.parquet has a
    day-level date but not holiday flags). Deferred to Phase 2C-C2-d/e where
    the panel is rebuilt to include weather (precipitation/snowfall) and can
    absorb holiday flags in the same pass.
    Concrete impact: of the 10 Friday-the-13th dates in 2019-2024, one
    (2021-08-13) falls on the first day of Obon.
  * cloud_cover NaN (~60 cells) filled with the panel median.
  * A Poisson QMLE fallback was NOT included — with alpha ~ 0.03 and 111k
    observations, non-convergence is not a realistic risk.

Outputs
-------
  output/prefecture_panel_results.json
    -> values[] uses the same _v() schema as truth.json (id/value/label/section/format)
    -> also embeds full coefficient tables and fit diagnostics under 'diagnostics'
    -> nb1 alpha (sensitivity to parameterization) reported alongside nb2 alpha
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "processed"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

PREF_ACC = DATA / "accidents_by_prefecture_daily.parquet"
PREF_CLD = DATA / "cloud_by_prefecture_daily.parquet"
BUR_ACC = DATA / "accidents_by_bureau_daily.parquet"
BUR_CLD = DATA / "cloud_by_bureau_daily.parquet"

DUMMY_COLS = ("prefecture_en", "year", "month", "weekday")
BUREAU_DUMMY_COLS = ("pref_code", "year", "month", "weekday")
MAIN_EFFECTS = ("is_fri13", "is_13th", "cloud_cover")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_prefecture_panel() -> pd.DataFrame:
    """Return (date, prefecture_en) panel joined with cloud_cover."""
    acc = pd.read_parquet(PREF_ACC)
    cld = pd.read_parquet(PREF_CLD)[["date", "prefecture_en", "cloud_cover"]]
    df = acc.merge(cld, on=["date", "prefecture_en"], how="left")
    _finalize_covariates(df)
    return df


def load_bureau_panel() -> pd.DataFrame:
    """Return (date, pref_code) panel joined with cloud_cover."""
    acc = pd.read_parquet(BUR_ACC)
    cld = pd.read_parquet(BUR_CLD)[["date", "pref_code", "cloud_cover"]]
    df = acc.merge(cld, on=["date", "pref_code"], how="left")
    _finalize_covariates(df)
    return df


def _finalize_covariates(df: pd.DataFrame) -> None:
    """Fill cloud_cover NaN with the panel median in place."""
    med = df["cloud_cover"].median()
    df["cloud_cover"] = df["cloud_cover"].fillna(med).astype(float)


def build_design(df: pd.DataFrame, fe_cols: tuple[str, ...]) -> tuple[pd.DataFrame, pd.Series]:
    """Assemble design matrix and endog vector.

    exog = const + is_fri13 + is_13th + cloud_cover + drop-first dummies for each FE column.
    """
    parts = [df[list(MAIN_EFFECTS)].astype(float)]
    for col in fe_cols:
        d = pd.get_dummies(df[col], prefix=col, drop_first=True).astype(float)
        parts.append(d)
    X = pd.concat(parts, axis=1)
    X = sm.add_constant(X, has_constant="add")
    y = df["total_count"].astype(float)
    return X, y


def build_cluster_groups(df: pd.DataFrame) -> np.ndarray:
    """Return (nobs, 2) group matrix for two-way clustering on (prefecture, date).

    Sensitivity model uses prefecture_en (47) rather than pref_code (51) even
    when its FE is at bureau level: Hokkaido's 5 bureau-rows share the same
    prefecture cluster to absorb any Hokkaido-wide non-weather correlated shock.
    """
    pref_id = pd.Categorical(df["prefecture_en"]).codes.astype(np.int64)
    date_id = df["date"].astype("int64").values
    return np.column_stack([pref_id, date_id])


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def fit_nb_panel(
    y: pd.Series,
    X: pd.DataFrame,
    groups_2d: np.ndarray,
    label: str,
) -> dict:
    """Fit NB2 MLE with Poisson warm start and two-way cluster-robust SE.

    Raises RuntimeError if either the Poisson warm-start, the NB MLE, or the
    cluster refit fails to converge; the caller must not fall back silently.
    """
    poisson = sm.Poisson(y, X).fit(disp=False, maxiter=200)
    _require_converged(poisson, f"{label}: Poisson warm start")
    start = np.concatenate([poisson.params.values, [1.0]])

    nb = NegativeBinomial(y, X, loglike_method="nb2")
    fit_iid = nb.fit(start_params=start, disp=False, maxiter=500)
    _require_converged(fit_iid, f"{label}: NB MLE (iid)")

    fit_c = nb.fit(
        start_params=fit_iid.params.values,
        cov_type="cluster",
        cov_kwds={"groups": groups_2d},
        disp=False,
        maxiter=50,
    )
    _require_converged(fit_c, f"{label}: NB MLE (two-way cluster refit)")

    nb1_alpha = _fit_nb1_alpha(y, X, start, label)

    return {
        "label": label,
        "family": "NegativeBinomial(nb2)",
        "n_obs": int(fit_iid.nobs),
        "k_params": int(len(fit_iid.params)),
        "alpha_mle_nb2": float(fit_iid.params["alpha"]),
        "alpha_mle_nb1": nb1_alpha,
        "poisson_llf": float(poisson.llf),
        "nb_llf": float(fit_iid.llf),
        "iid_se": _extract(fit_iid, "iid"),
        "cluster_se": _extract(fit_c, "cluster_2way_pref_date"),
        "n_clusters_pref": int(len(np.unique(groups_2d[:, 0]))),
        "n_clusters_date": int(len(np.unique(groups_2d[:, 1]))),
        "converged": True,
    }


def _fit_nb1_alpha(y: pd.Series, X: pd.DataFrame, start: np.ndarray, label: str) -> float | None:
    """Refit NB with nb1 parameterization to report alpha sensitivity to spec.

    Returns None on non-convergence — nb1 is diagnostic only, not blocking.
    """
    try:
        nb1 = NegativeBinomial(y, X, loglike_method="nb1")
        fit1 = nb1.fit(start_params=start, disp=False, maxiter=500)
        if fit1.mle_retvals.get("converged", False):
            return float(fit1.params["alpha"])
    except Exception as exc:
        print(f"  [{label}] nb1 refit skipped: {type(exc).__name__}: {exc}", flush=True)
    return None


def _require_converged(fit, label: str) -> None:
    """Raise if a statsmodels fit did not converge cleanly."""
    if hasattr(fit, "mle_retvals"):
        if not fit.mle_retvals.get("converged", False):
            raise RuntimeError(f"{label} did not converge: {fit.mle_retvals}")


def _extract(fit, se_source: str) -> dict:
    """Pull is_fri13 coef/SE/CI from a fit."""
    coef = float(fit.params["is_fri13"])
    se = float(fit.bse["is_fri13"])
    if not (se > 0 and math.isfinite(se)):
        raise RuntimeError(f"Non-positive/non-finite SE from {se_source}: {se}")
    z = coef / se
    ratio = math.exp(coef)
    ci_low = math.exp(coef - 1.96 * se)
    ci_high = math.exp(coef + 1.96 * se)
    pval = float(fit.pvalues["is_fri13"])
    return {
        "se_source": se_source,
        "is_fri13_coef": coef,
        "is_fri13_se": se,
        "is_fri13_z": z,
        "is_fri13_p": pval,
        "count_ratio": ratio,
        "count_ratio_ci_low": ci_low,
        "count_ratio_ci_high": ci_high,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def _v(id_: str, value, label: str, section: str, fmt: str = ".2f") -> dict:
    return {"id": id_, "value": value, "label": label, "section": section, "format": fmt}


def build_truth_values(primary: dict, sensitivity: dict) -> list[dict]:
    """Emit truth.json-shaped entries for manuscript verification."""
    v = []

    # Primary (47 prefecture FE)
    v.append(_v("pref_nb_alpha_nb2", primary["alpha_mle_nb2"],
                "Prefecture panel NB2 MLE alpha", "methods", ".4f"))
    if primary["alpha_mle_nb1"] is not None:
        v.append(_v("pref_nb_alpha_nb1", primary["alpha_mle_nb1"],
                    "Prefecture panel NB1 MLE alpha (sensitivity)", "methods", ".4f"))
    v.append(_v("pref_nb_n_obs", primary["n_obs"],
                "Prefecture panel N observations", "methods", "d"))
    v.append(_v("pref_nb_n_clusters_pref", primary["n_clusters_pref"],
                "Prefecture panel N prefecture clusters", "methods", "d"))
    v.append(_v("pref_nb_n_clusters_date", primary["n_clusters_date"],
                "Prefecture panel N date clusters", "methods", "d"))
    v.append(_v("pref_nb_k_params", primary["k_params"],
                "Prefecture panel N parameters", "methods", "d"))

    prim_cl = primary["cluster_se"]
    v.append(_v("pref_nb_coef", prim_cl["is_fri13_coef"],
                "Prefecture panel NB coefficient (is_fri13)", "results", ".4f"))
    v.append(_v("pref_nb_se_cluster", prim_cl["is_fri13_se"],
                "Prefecture panel two-way cluster SE (is_fri13)", "results", ".4f"))
    v.append(_v("pref_nb_count_ratio", prim_cl["count_ratio"],
                "Prefecture panel count ratio (is_fri13)", "results", ".2f"))
    v.append(_v("pref_nb_ci_low", prim_cl["count_ratio_ci_low"],
                "Prefecture panel count ratio 95% CI lower", "results", ".2f"))
    v.append(_v("pref_nb_ci_high", prim_cl["count_ratio_ci_high"],
                "Prefecture panel count ratio 95% CI upper", "results", ".2f"))
    v.append(_v("pref_nb_p", prim_cl["is_fri13_p"],
                "Prefecture panel p-value (is_fri13, two-way cluster SE)", "results", ".3f"))

    # Sensitivity (51 bureau FE, same cluster axis as primary)
    v.append(_v("bureau_nb_alpha_nb2", sensitivity["alpha_mle_nb2"],
                "Bureau panel NB2 MLE alpha", "methods", ".4f"))
    if sensitivity["alpha_mle_nb1"] is not None:
        v.append(_v("bureau_nb_alpha_nb1", sensitivity["alpha_mle_nb1"],
                    "Bureau panel NB1 MLE alpha (sensitivity)", "methods", ".4f"))
    v.append(_v("bureau_nb_n_obs", sensitivity["n_obs"],
                "Bureau panel N observations", "methods", "d"))
    v.append(_v("bureau_nb_n_clusters_pref", sensitivity["n_clusters_pref"],
                "Bureau panel N prefecture clusters (Hokkaido combined)", "methods", "d"))

    sens_cl = sensitivity["cluster_se"]
    v.append(_v("bureau_nb_coef", sens_cl["is_fri13_coef"],
                "Bureau panel coefficient (is_fri13)", "results", ".4f"))
    v.append(_v("bureau_nb_se_cluster", sens_cl["is_fri13_se"],
                "Bureau panel two-way cluster SE (is_fri13)", "results", ".4f"))
    v.append(_v("bureau_nb_count_ratio", sens_cl["count_ratio"],
                "Bureau panel count ratio (is_fri13)", "results", ".2f"))
    v.append(_v("bureau_nb_ci_low", sens_cl["count_ratio_ci_low"],
                "Bureau panel count ratio 95% CI lower", "results", ".2f"))
    v.append(_v("bureau_nb_ci_high", sens_cl["count_ratio_ci_high"],
                "Bureau panel count ratio 95% CI upper", "results", ".2f"))
    v.append(_v("bureau_nb_p", sens_cl["is_fri13_p"],
                "Bureau panel p-value (is_fri13, two-way cluster SE)", "results", ".3f"))

    return v


def write_results(primary: dict, sensitivity: dict, out_path: Path) -> None:
    doc = {
        "project": "friday13th",
        "phase": "2C-C2-c",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "script": "src/02_prefecture_panel_nb.py",
        "values": build_truth_values(primary, sensitivity),
        "diagnostics": {
            "primary_47_prefecture": primary,
            "sensitivity_51_bureau": sensitivity,
        },
    }
    # allow_nan=False so a NaN accidentally reaching the writer raises loudly
    # rather than producing non-RFC-8259-conformant JSON.
    out_path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_primary() -> dict:
    df = load_prefecture_panel()
    X, y = build_design(df, DUMMY_COLS)
    groups = build_cluster_groups(df)
    print(f"[primary] rows={len(df):,} cols={X.shape[1]} "
          f"pref-clusters={len(np.unique(groups[:,0]))} date-clusters={len(np.unique(groups[:,1]))}",
          flush=True)
    return fit_nb_panel(y, X, groups, label="prefecture_47_FE")


def run_sensitivity() -> dict:
    df = load_bureau_panel()
    X, y = build_design(df, BUREAU_DUMMY_COLS)
    # Cluster on prefecture_en (47), not pref_code (51): the sensitivity varies
    # ONLY the FE granularity, not the cluster axis. Hokkaido stays combined.
    groups = build_cluster_groups(df)
    print(f"[sensitivity] rows={len(df):,} cols={X.shape[1]} "
          f"pref-clusters={len(np.unique(groups[:,0]))} date-clusters={len(np.unique(groups[:,1]))}",
          flush=True)
    return fit_nb_panel(y, X, groups, label="bureau_51_FE")


def main() -> None:
    print("Prefecture panel NB (primary) ...", flush=True)
    primary = run_primary()
    _report(primary, "Primary: 47 prefecture FE NB MLE (two-way cluster: pref+date)")

    print("\nBureau panel NB (sensitivity) ...", flush=True)
    sensitivity = run_sensitivity()
    _report(sensitivity, "Sensitivity: 51 bureau FE NB MLE (two-way cluster: pref+date)")

    out_path = OUTPUT / "prefecture_panel_results.json"
    write_results(primary, sensitivity, out_path)
    print(f"\nWrote {out_path}", flush=True)


def _report(result: dict, header: str) -> None:
    print(f"\n=== {header} ===")
    print(f"  n_obs: {result['n_obs']:,}  k_params: {result['k_params']}  "
          f"pref-clusters: {result['n_clusters_pref']}  date-clusters: {result['n_clusters_date']}")
    print(f"  MLE alpha (nb2): {result['alpha_mle_nb2']:.4f}"
          f"  (nb1 sensitivity: {result['alpha_mle_nb1']!r})")
    for src, block in [("iid", result["iid_se"]), ("2way-cluster", result["cluster_se"])]:
        b = block
        print(f"  [{src}] coef={b['is_fri13_coef']:+.4f}  SE={b['is_fri13_se']:.4f}"
              f"  z={b['is_fri13_z']:+.2f}  p={b['is_fri13_p']:.3f}"
              f"  ratio={b['count_ratio']:.4f} "
              f"CI[{b['count_ratio_ci_low']:.4f},{b['count_ratio_ci_high']:.4f}]")


if __name__ == "__main__":
    sys.exit(main())
