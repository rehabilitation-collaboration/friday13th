"""03_prefecture_panel_weather_nb.py

Phase 2C-C2-e:
Prefecture- and bureau-level NB panel regression with weather (precipitation,
snowfall, snow_depth) AND holiday / obon / newyear flags added to the design.
Template is 02_prefecture_panel_nb.py; 02 is deliberately untouched — the
parallel-reporting strategy (per handoff Key Decisions) keeps 2C-c "unadjusted"
and 2C-e "weather+holiday adjusted" both alive in the manuscript.

Additions vs 02
---------------
  + MAIN_EFFECTS: precipitation_mm, snowfall_cm, snow_depth_max_cm,
                  is_holiday, is_obon, is_newyear
  + listwise deletion of rows where any weather covariate is null.
    The raw master cache had 16 rows / 5 stations with any-null weather
    covariate: 15 rows precipitation_mm null across 4 stations
    (47615×10 in Jul-Aug 2022 following a heavy-rain sequence — consistent
    with rain-gauge saturation MNAR, worth acknowledging in Limitations;
    plus 47607×2 / 47813×2 / 47605×1) and 1 row snow_depth_max_cm null at
    station 47807 on 2022-11-10. Total 0.014% of the master cache.
    Fillna(0) is unsafe because station 47605 on 2022-12-19 has
    snowfall_cm=13 with precipitation_mm=NaN — snow is precipitation, so
    zeroing the missing rainfall would systematically understate winter
    precipitation on snow days. Listwise is safer and 0.014% is negligible.
  + snow_depth_max_cm multicollinearity pre-checked before inclusion:
    |max corr(snow_depth, month_dummy)| = 0.15 (well under 0.7 threshold),
    VIF = 1.42 (well under 5). No winter-leak concern; main-model safe.
  + is_holiday sourced from Cabinet Office CSV
    (data/jp_holidays_2019_2024.csv, 111 dates). is_obon = 8/13-16 hardcode.
    is_newyear = 1/1-3 hardcode. See 01a_build_panels.py.
  + Diff report vs 2C-c results embedded in the JSON output.
  + nb1 sensitivity refit now extracts is_fri13 count_ratio (not just alpha)
    so the primary parameter of interest is verifiable across nb1/nb2
    parameterizations (Phase 2C-C2-e P2-4 fix).
  + nb2 fit_iid RuntimeWarnings are captured and reported in the JSON
    diagnostics instead of being silently emitted to stderr (Phase 2C-C2-e
    P2-2 fix). Empty list means the fit was numerically clean.

Rationale (2021-08-13 Obon-initial × Fri13 collision)
-----------------------------------------------------
  Of the 10 Fri13 dates in 2019-2024, only 2021-08-13 falls on Obon initial
  day. The regenerated panel shows this date at 713 accidents versus 863-1343
  on the other nine Fri13 dates — a stark outlier consistent with Obon
  travel-volume reduction. Without is_obon, this pulls the is_fri13
  coefficient downward. is_obon isolates that effect so the is_fri13 estimate
  reflects the Friday-the-13th-specific increment net of Obon.

Model
-----
  endog = total_count
  exog  = is_fri13 + is_13th
          + is_holiday + is_obon + is_newyear
          + cloud_cover + precipitation_mm + snowfall_cm + snow_depth_max_cm
          + prefecture FE + year FE + month FE + weekday FE
  loglike_method = 'nb2'; Poisson warm start; MLE alpha; two-way cluster SE
  (prefecture + date).

Outputs
-------
  output/weather_holiday_nb_results.json   (kept separate from 2C-c results
                                            so both survive for manuscript
                                            parallel reporting).
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
from statsmodels.discrete.discrete_model import NegativeBinomial

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "processed"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

PREF_ACC = DATA / "accidents_by_prefecture_daily.parquet"
PREF_CLD = DATA / "cloud_by_prefecture_daily.parquet"
PREF_WTH = DATA / "weather_by_prefecture_daily.parquet"
BUR_ACC = DATA / "accidents_by_bureau_daily.parquet"
BUR_CLD = DATA / "cloud_by_bureau_daily.parquet"
BUR_WTH = DATA / "weather_by_bureau_daily.parquet"

PRIOR_RESULTS = OUTPUT / "prefecture_panel_results.json"

DUMMY_COLS = ("prefecture_en", "year", "month", "weekday")
BUREAU_DUMMY_COLS = ("pref_code", "year", "month", "weekday")
WEATHER_COLS = ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")
HOLIDAY_COLS = ("is_holiday", "is_obon", "is_newyear")
MAIN_EFFECTS = (
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


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_prefecture_panel() -> pd.DataFrame:
    """(date, prefecture_en) panel joined with cloud_cover + weather."""
    acc = pd.read_parquet(PREF_ACC)
    cld = pd.read_parquet(PREF_CLD)[["date", "prefecture_en", "cloud_cover"]]
    wth = pd.read_parquet(PREF_WTH)[
        ["date", "prefecture_en", *WEATHER_COLS]
    ]
    df = (
        acc.merge(cld, on=["date", "prefecture_en"], how="left")
           .merge(wth, on=["date", "prefecture_en"], how="left")
    )
    df = _finalize_covariates(df, level="prefecture")
    return df


def load_bureau_panel() -> pd.DataFrame:
    """(date, pref_code) panel joined with cloud_cover + weather."""
    acc = pd.read_parquet(BUR_ACC)
    cld = pd.read_parquet(BUR_CLD)[["date", "pref_code", "cloud_cover"]]
    wth = pd.read_parquet(BUR_WTH)[
        ["date", "pref_code", *WEATHER_COLS]
    ]
    df = (
        acc.merge(cld, on=["date", "pref_code"], how="left")
           .merge(wth, on=["date", "pref_code"], how="left")
    )
    df = _finalize_covariates(df, level="bureau")
    return df


def _finalize_covariates(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """cloud_cover NaN → panel median (~60 cells); weather NaN → listwise.

    Listwise chosen over fillna(0) for weather because snowfall_cm > 0 with
    precipitation_mm = NaN co-occur (station 47605 on 2022-12-19). Zero-fill
    would understate winter precipitation on snow days.
    """
    med = df["cloud_cover"].median()
    df["cloud_cover"] = df["cloud_cover"].fillna(med).astype(float)

    before = len(df)
    weather_na = df[list(WEATHER_COLS)].isna().any(axis=1)
    n_drop = int(weather_na.sum())
    if n_drop:
        print(
            f"  [{level}] listwise deletion: {n_drop} rows dropped "
            f"({n_drop / before * 100:.4f}%) — any-null in "
            f"{list(WEATHER_COLS)}",
            flush=True,
        )
    df = df.loc[~weather_na].copy()
    for c in WEATHER_COLS:
        df[c] = df[c].astype(float)
    return df.reset_index(drop=True)


def build_design(df: pd.DataFrame, fe_cols: tuple[str, ...]) -> tuple[pd.DataFrame, pd.Series]:
    """exog = const + MAIN_EFFECTS + drop-first dummies for each FE column."""
    parts = [df[list(MAIN_EFFECTS)].astype(float)]
    for col in fe_cols:
        d = pd.get_dummies(df[col], prefix=col, drop_first=True).astype(float)
        parts.append(d)
    X = pd.concat(parts, axis=1)
    X = sm.add_constant(X, has_constant="add")
    y = df["total_count"].astype(float)
    return X, y


def build_cluster_groups(df: pd.DataFrame) -> np.ndarray:
    """(nobs, 2) group matrix for two-way clustering on (prefecture, date)."""
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
    """NB2 MLE + Poisson warm start + two-way cluster-robust SE.

    RuntimeWarnings emitted by statsmodels during the nb2 iid MLE are captured
    (not suppressed) and returned in `nb2_runtime_warnings` so downstream
    diagnostics see numerical instability instead of silent stderr output
    (Phase 2C-C2-e P2-2 fix).
    """
    poisson = sm.Poisson(y, X).fit(disp=False, maxiter=200)
    _require_converged(poisson, f"{label}: Poisson warm start")
    start = np.concatenate([poisson.params.values, [1.0]])

    nb = NegativeBinomial(y, X, loglike_method="nb2")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        fit_iid = nb.fit(start_params=start, disp=False, maxiter=500)
    nb2_warnings = sorted({
        str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)
    })
    _require_converged(fit_iid, f"{label}: NB MLE (iid)")

    fit_c = nb.fit(
        start_params=fit_iid.params.values,
        cov_type="cluster",
        cov_kwds={"groups": groups_2d},
        disp=False,
        maxiter=50,
    )
    _require_converged(fit_c, f"{label}: NB MLE (two-way cluster refit)")

    nb1_diag = _fit_nb1_diag(y, X, start, label)

    return {
        "label": label,
        "family": "NegativeBinomial(nb2)",
        "n_obs": int(fit_iid.nobs),
        "k_params": int(len(fit_iid.params)),
        "alpha_mle_nb2": float(fit_iid.params["alpha"]),
        "alpha_mle_nb1": nb1_diag["alpha"] if nb1_diag else None,
        "is_fri13_ratio_nb1": nb1_diag["is_fri13_count_ratio"] if nb1_diag else None,
        "nb2_runtime_warnings": nb2_warnings,
        "poisson_llf": float(poisson.llf),
        "nb_llf": float(fit_iid.llf),
        "iid_se": _extract(fit_iid, "iid"),
        "cluster_se": _extract(fit_c, "cluster_2way_pref_date"),
        "n_clusters_pref": int(len(np.unique(groups_2d[:, 0]))),
        "n_clusters_date": int(len(np.unique(groups_2d[:, 1]))),
        "weather_coefs": _extract_weather_holiday_coefs(fit_c),
        "converged": True,
    }


def _fit_nb1_diag(y: pd.Series, X: pd.DataFrame, start: np.ndarray, label: str) -> dict | None:
    """Refit NB with nb1 parameterization; report BOTH alpha AND the is_fri13
    count_ratio so reviewers can verify the primary parameter of interest is
    robust to the nb2/nb1 parameterization choice (alpha itself often is not;
    the is_fri13 count_ratio should be — 2C-e empirical: nb1 1.0275 vs nb2
    1.0248, ~0.3% divergence). Returns None on non-convergence."""
    try:
        nb1 = NegativeBinomial(y, X, loglike_method="nb1")
        fit1 = nb1.fit(start_params=start, disp=False, maxiter=500)
        if not fit1.mle_retvals.get("converged", False):
            return None
        coef = float(fit1.params["is_fri13"])
        return {
            "alpha": float(fit1.params["alpha"]),
            "is_fri13_coef": coef,
            "is_fri13_count_ratio": math.exp(coef),
        }
    except Exception as exc:
        print(f"  [{label}] nb1 refit skipped: {type(exc).__name__}: {exc}", flush=True)
        return None


def _require_converged(fit, label: str) -> None:
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


def _extract_weather_holiday_coefs(fit) -> dict:
    """Coef / SE / count ratio for every non-Fri13 MAIN_EFFECT so we can
    report how big the confounders were (and confirm is_obon is negative)."""
    out = {}
    for name in MAIN_EFFECTS:
        if name == "is_fri13":
            continue
        if name not in fit.params.index:
            continue
        coef = float(fit.params[name])
        se = float(fit.bse[name])
        out[name] = {
            "coef": coef,
            "se": se,
            "count_ratio": math.exp(coef),
            "p": float(fit.pvalues[name]),
        }
    return out


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def _v(id_: str, value, label: str, section: str, fmt: str = ".2f") -> dict:
    return {"id": id_, "value": value, "label": label, "section": section, "format": fmt}


def build_truth_values(primary: dict, sensitivity: dict) -> list[dict]:
    """truth.json-shaped entries for manuscript verification (2C-e version)."""
    v = []

    # Primary (47 prefecture FE, weather+holiday adjusted)
    v.append(_v("pref_nb_wh_alpha_nb2", primary["alpha_mle_nb2"],
                "Prefecture panel NB2 MLE alpha (weather+holiday)", "methods", ".4f"))
    if primary["alpha_mle_nb1"] is not None:
        v.append(_v("pref_nb_wh_alpha_nb1", primary["alpha_mle_nb1"],
                    "Prefecture panel NB1 MLE alpha (weather+holiday, sensitivity)", "methods", ".4f"))
    if primary["is_fri13_ratio_nb1"] is not None:
        v.append(_v("pref_nb_wh_ratio_nb1", primary["is_fri13_ratio_nb1"],
                    "Prefecture panel is_fri13 count ratio under NB1 (weather+holiday, robustness)", "methods", ".4f"))
    v.append(_v("pref_nb_wh_n_obs", primary["n_obs"],
                "Prefecture panel N observations (weather+holiday)", "methods", "d"))
    v.append(_v("pref_nb_wh_n_clusters_pref", primary["n_clusters_pref"],
                "Prefecture panel N prefecture clusters (weather+holiday)", "methods", "d"))
    v.append(_v("pref_nb_wh_n_clusters_date", primary["n_clusters_date"],
                "Prefecture panel N date clusters (weather+holiday)", "methods", "d"))
    v.append(_v("pref_nb_wh_k_params", primary["k_params"],
                "Prefecture panel N parameters (weather+holiday)", "methods", "d"))

    prim_cl = primary["cluster_se"]
    v.append(_v("pref_nb_wh_coef", prim_cl["is_fri13_coef"],
                "Prefecture panel NB coefficient (is_fri13, weather+holiday)", "results", ".4f"))
    v.append(_v("pref_nb_wh_se_cluster", prim_cl["is_fri13_se"],
                "Prefecture panel two-way cluster SE (is_fri13, weather+holiday)", "results", ".4f"))
    v.append(_v("pref_nb_wh_count_ratio", prim_cl["count_ratio"],
                "Prefecture panel count ratio (is_fri13, weather+holiday)", "results", ".2f"))
    v.append(_v("pref_nb_wh_ci_low", prim_cl["count_ratio_ci_low"],
                "Prefecture panel count ratio 95% CI lower (weather+holiday)", "results", ".2f"))
    v.append(_v("pref_nb_wh_ci_high", prim_cl["count_ratio_ci_high"],
                "Prefecture panel count ratio 95% CI upper (weather+holiday)", "results", ".2f"))
    v.append(_v("pref_nb_wh_p", prim_cl["is_fri13_p"],
                "Prefecture panel p-value (is_fri13, weather+holiday, two-way cluster SE)", "results", ".3f"))

    # Sensitivity (51 bureau FE, weather+holiday)
    v.append(_v("bureau_nb_wh_alpha_nb2", sensitivity["alpha_mle_nb2"],
                "Bureau panel NB2 MLE alpha (weather+holiday)", "methods", ".4f"))
    if sensitivity["is_fri13_ratio_nb1"] is not None:
        v.append(_v("bureau_nb_wh_ratio_nb1", sensitivity["is_fri13_ratio_nb1"],
                    "Bureau panel is_fri13 count ratio under NB1 (weather+holiday, robustness)", "methods", ".4f"))
    v.append(_v("bureau_nb_wh_n_obs", sensitivity["n_obs"],
                "Bureau panel N observations (weather+holiday)", "methods", "d"))
    v.append(_v("bureau_nb_wh_n_clusters_pref", sensitivity["n_clusters_pref"],
                "Bureau panel N prefecture clusters (Hokkaido combined, weather+holiday)", "methods", "d"))

    sens_cl = sensitivity["cluster_se"]
    v.append(_v("bureau_nb_wh_coef", sens_cl["is_fri13_coef"],
                "Bureau panel coefficient (is_fri13, weather+holiday)", "results", ".4f"))
    v.append(_v("bureau_nb_wh_se_cluster", sens_cl["is_fri13_se"],
                "Bureau panel two-way cluster SE (is_fri13, weather+holiday)", "results", ".4f"))
    v.append(_v("bureau_nb_wh_count_ratio", sens_cl["count_ratio"],
                "Bureau panel count ratio (is_fri13, weather+holiday)", "results", ".2f"))
    v.append(_v("bureau_nb_wh_ci_low", sens_cl["count_ratio_ci_low"],
                "Bureau panel count ratio 95% CI lower (weather+holiday)", "results", ".2f"))
    v.append(_v("bureau_nb_wh_ci_high", sens_cl["count_ratio_ci_high"],
                "Bureau panel count ratio 95% CI upper (weather+holiday)", "results", ".2f"))
    v.append(_v("bureau_nb_wh_p", sens_cl["is_fri13_p"],
                "Bureau panel p-value (is_fri13, weather+holiday, two-way cluster SE)", "results", ".3f"))

    return v


def diff_vs_prior(primary: dict, sensitivity: dict) -> dict | None:
    """Compare Fri13 estimates to the 2C-c 'unadjusted' baseline stored in
    prefecture_panel_results.json. Returns None if the baseline is missing."""
    if not PRIOR_RESULTS.exists():
        return None
    prior = json.loads(PRIOR_RESULTS.read_text(encoding="utf-8"))
    prior_vals = {e["id"]: e["value"] for e in prior.get("values", [])}

    def _delta(new: dict, prefix: str) -> dict:
        return {
            "prior_count_ratio": prior_vals.get(f"{prefix}_count_ratio"),
            "new_count_ratio": new["cluster_se"]["count_ratio"],
            "delta_count_ratio": (
                new["cluster_se"]["count_ratio"]
                - prior_vals.get(f"{prefix}_count_ratio", float("nan"))
            ),
            "prior_ci": [
                prior_vals.get(f"{prefix}_ci_low"),
                prior_vals.get(f"{prefix}_ci_high"),
            ],
            "new_ci": [
                new["cluster_se"]["count_ratio_ci_low"],
                new["cluster_se"]["count_ratio_ci_high"],
            ],
            "prior_p": prior_vals.get(f"{prefix}_p"),
            "new_p": new["cluster_se"]["is_fri13_p"],
        }

    return {
        "prior_source": str(PRIOR_RESULTS.name),
        "prior_phase": prior.get("phase"),
        "primary_47_prefecture": _delta(primary, "pref_nb"),
        "sensitivity_51_bureau": _delta(sensitivity, "bureau_nb"),
    }


def write_results(primary: dict, sensitivity: dict, out_path: Path) -> None:
    diff = diff_vs_prior(primary, sensitivity)
    doc = {
        "project": "friday13th",
        "phase": "2C-C2-e",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "script": "src/03_prefecture_panel_weather_nb.py",
        "adjustments": list(MAIN_EFFECTS[2:]),  # everything after is_fri13/is_13th
        "values": build_truth_values(primary, sensitivity),
        "diagnostics": {
            "primary_47_prefecture": primary,
            "sensitivity_51_bureau": sensitivity,
        },
        "diff_vs_2c_c_unadjusted": diff,
    }
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
          f"pref-clusters={len(np.unique(groups[:,0]))} "
          f"date-clusters={len(np.unique(groups[:,1]))}",
          flush=True)
    return fit_nb_panel(y, X, groups, label="prefecture_47_FE_weather_holiday")


def run_sensitivity() -> dict:
    df = load_bureau_panel()
    X, y = build_design(df, BUREAU_DUMMY_COLS)
    groups = build_cluster_groups(df)
    print(f"[sensitivity] rows={len(df):,} cols={X.shape[1]} "
          f"pref-clusters={len(np.unique(groups[:,0]))} "
          f"date-clusters={len(np.unique(groups[:,1]))}",
          flush=True)
    return fit_nb_panel(y, X, groups, label="bureau_51_FE_weather_holiday")


def _report(result: dict, header: str) -> None:
    print(f"\n=== {header} ===")
    print(f"  n_obs: {result['n_obs']:,}  k_params: {result['k_params']}  "
          f"pref-clusters: {result['n_clusters_pref']}  "
          f"date-clusters: {result['n_clusters_date']}")
    print(f"  MLE alpha (nb2): {result['alpha_mle_nb2']:.4f}  "
          f"(nb1 alpha: {result['alpha_mle_nb1']!r}, "
          f"nb1 is_fri13 ratio: {result['is_fri13_ratio_nb1']!r})")
    if result["nb2_runtime_warnings"]:
        print(f"  ⚠ nb2 fit_iid captured RuntimeWarnings: "
              f"{result['nb2_runtime_warnings']}")
    for src, block in [("iid", result["iid_se"]), ("2way-cluster", result["cluster_se"])]:
        b = block
        print(f"  [{src}] coef={b['is_fri13_coef']:+.4f}  SE={b['is_fri13_se']:.4f}"
              f"  z={b['is_fri13_z']:+.2f}  p={b['is_fri13_p']:.3f}"
              f"  ratio={b['count_ratio']:.4f} "
              f"CI[{b['count_ratio_ci_low']:.4f},{b['count_ratio_ci_high']:.4f}]")
    print(f"  [confounder coefs]")
    for name, block in result["weather_coefs"].items():
        print(f"    {name:<20s} coef={block['coef']:+.4f}  "
              f"SE={block['se']:.4f}  ratio={block['count_ratio']:.4f}  "
              f"p={block['p']:.3f}")


def _report_diff(diff: dict | None) -> None:
    if diff is None:
        print("\n(no prior 2C-c result found — skipping diff)")
        return
    print(f"\n=== Diff vs 2C-c unadjusted (prior phase={diff['prior_phase']}) ===")
    for name in ("primary_47_prefecture", "sensitivity_51_bureau"):
        d = diff[name]
        print(f"  [{name}]")
        print(f"    count_ratio  {d['prior_count_ratio']:.4f} → {d['new_count_ratio']:.4f}  "
              f"(Δ={d['delta_count_ratio']:+.4f})")
        print(f"    95% CI       [{d['prior_ci'][0]:.4f}, {d['prior_ci'][1]:.4f}] → "
              f"[{d['new_ci'][0]:.4f}, {d['new_ci'][1]:.4f}]")
        print(f"    p-value      {d['prior_p']:.3f} → {d['new_p']:.3f}")


def main() -> None:
    print("Prefecture panel NB (primary, weather+holiday) ...", flush=True)
    primary = run_primary()
    _report(primary, "Primary: 47 prefecture FE NB MLE + weather + holiday")

    print("\nBureau panel NB (sensitivity, weather+holiday) ...", flush=True)
    sensitivity = run_sensitivity()
    _report(sensitivity, "Sensitivity: 51 bureau FE NB MLE + weather + holiday")

    out_path = OUTPUT / "weather_holiday_nb_results.json"
    write_results(primary, sensitivity, out_path)
    print(f"\nWrote {out_path}", flush=True)

    diff = diff_vs_prior(primary, sensitivity)
    _report_diff(diff)


if __name__ == "__main__":
    sys.exit(main())
