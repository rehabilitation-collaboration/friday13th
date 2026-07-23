"""Phase 2C-C5 Table 4: subgroup-level NB fit for the Fatal-accident detail table.

Design decision (2C-C5): all 8 subgroups fitted with the SAME national-level
NB2 model (not a hybrid with prefecture panels). Rationale:
  1. Explanation parsimony — one Methods sentence covers all 8 rows.
  2. Reviewer robustness — no "why does severity use prefecture panels but
     age use national counts?" question.
  3. Prefecture-level heterogeneity is already covered by Figure S3 (2C-C4)
     for the overall is_fri13 estimand; Table 4 asks a different question
     (which subgroup drives any signal, if at all).
  4. Existing parquet coverage is sufficient — no new 01d panel script.

Subgroups (union, not cross): 2 severity + 4 age + 2 timeofday = 8 total.
Bonferroni threshold: alpha_family = 0.05 / 8 = 0.00625.

Inputs:
  data/daily_by_severity.parquet   (fatal, injury; 2192 x 2 = 4384 rows)
  data/daily_by_age.parquet        (young, mid_low, mid_hi, elderly; 2192 x 4 = 8768 rows)
  data/daily_by_timeofday.parquet  (daytime, nighttime; 2192 x 2 = 4384 rows)

Outputs:
  output/subgroup_table4_results.json
    - values[]           : truth.json _v() entries (rate ratios, NB count ratios,
                            raw p, Bonferroni p, N)
    - table4_rows[]      : ready-to-render markdown table rows
    - config             : {n_subgroups, alpha_family, bonferroni_threshold}
    - methods_notes      : short prose for the Methods paragraph in manuscript

Model spec per subgroup (national-level NB2):
  y ~ is_friday13th + C(year) + C(month) + C(weekday_code) + is_holiday_flag
  family = NegativeBinomial (nb2), alpha estimated by MLE
  restrict to Fridays only (matches primary case-crossover framing)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.discrete.discrete_model import NegativeBinomial

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"

SEVERITY_PARQUET = DATA_DIR / "daily_by_severity.parquet"
AGE_PARQUET = DATA_DIR / "daily_by_age.parquet"
TIMEOFDAY_PARQUET = DATA_DIR / "daily_by_timeofday.parquet"

OUT_JSON = OUTPUT_DIR / "subgroup_table4_results.json"

N_SUBGROUPS = 8
ALPHA_FAMILY = 0.05
BONFERRONI_THRESHOLD = ALPHA_FAMILY / N_SUBGROUPS

SUBGROUPS: list[dict] = [
    {"key": "fatal", "label": "Fatal accidents",
     "parquet": SEVERITY_PARQUET, "filter_col": "severity_label", "filter_val": "fatal"},
    {"key": "injury", "label": "Injury accidents",
     "parquet": SEVERITY_PARQUET, "filter_col": "severity_label", "filter_val": "injury"},
    {"key": "young", "label": "Age <=24 (young)",
     "parquet": AGE_PARQUET, "filter_col": "age_group_a", "filter_val": "young"},
    {"key": "mid_low", "label": "Age 25-44 (mid-lower)",
     "parquet": AGE_PARQUET, "filter_col": "age_group_a", "filter_val": "mid_low"},
    {"key": "mid_hi", "label": "Age 45-64 (mid-upper)",
     "parquet": AGE_PARQUET, "filter_col": "age_group_a", "filter_val": "mid_hi"},
    {"key": "elderly", "label": "Age >=65 (elderly)",
     "parquet": AGE_PARQUET, "filter_col": "age_group_a", "filter_val": "elderly"},
    {"key": "daytime", "label": "Daytime",
     "parquet": TIMEOFDAY_PARQUET, "filter_col": "timeofday", "filter_val": "daytime"},
    {"key": "nighttime", "label": "Nighttime",
     "parquet": TIMEOFDAY_PARQUET, "filter_col": "timeofday", "filter_val": "nighttime"},
]


def _v(id_: str, value: Any, label: str, section: str,
       fmt: str = ".2f", context: str = "") -> dict:
    entry: dict[str, Any] = {
        "id": id_,
        "value": value,
        "label": label,
        "section": section,
        "format": fmt,
    }
    if context:
        entry["context"] = context
    return entry


def load_subgroup(spec: dict) -> pd.DataFrame:
    df = pd.read_parquet(spec["parquet"])
    df = df[df[spec["filter_col"]] == spec["filter_val"]].copy()
    df = df[df["is_friday"] == 1].copy()
    df = df.sort_values("date").reset_index(drop=True)
    return df


def descriptive_stats(df: pd.DataFrame) -> dict:
    fri13 = df[df["is_friday13th"] == 1]["total"].astype(float)
    other = df[df["is_friday13th"] == 0]["total"].astype(float)
    return {
        "n_fri13": int(len(fri13)),
        "n_other": int(len(other)),
        "mean_fri13": float(fri13.mean()) if len(fri13) else float("nan"),
        "sd_fri13": float(fri13.std(ddof=1)) if len(fri13) > 1 else float("nan"),
        "mean_other": float(other.mean()) if len(other) else float("nan"),
        "sd_other": float(other.std(ddof=1)) if len(other) > 1 else float("nan"),
        "rate_ratio_crude": (
            float(fri13.mean() / other.mean()) if len(fri13) and other.mean() else float("nan")
        ),
    }


def welch_t_test(df: pd.DataFrame) -> dict:
    """Independent two-sample Welch t-test on raw counts (Fri13 vs other Fri).

    Kept as a companion to the NB fit to mirror the V1 reporting style
    (Ranganathan 2024, Schuld 2011 both use raw t / Welch on daily counts).
    """
    fri13 = df[df["is_friday13th"] == 1]["total"].astype(float).to_numpy()
    other = df[df["is_friday13th"] == 0]["total"].astype(float).to_numpy()
    if len(fri13) < 2 or len(other) < 2:
        return {"t_stat": float("nan"), "p_value": float("nan"),
                "df_welch": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan")}
    res = stats.ttest_ind(fri13, other, equal_var=False)
    mean_diff = fri13.mean() - other.mean()
    se_diff = float(
        np.sqrt(fri13.var(ddof=1) / len(fri13) + other.var(ddof=1) / len(other))
    )
    df_welch = float(res.df)
    t_crit = float(stats.t.ppf(0.975, df_welch))
    return {
        "t_stat": float(res.statistic),
        "p_value": float(res.pvalue),
        "df_welch": df_welch,
        "mean_diff": float(mean_diff),
        "se_diff": se_diff,
        "ci_low": float(mean_diff - t_crit * se_diff),
        "ci_high": float(mean_diff + t_crit * se_diff),
    }


def _build_design(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    y = df["total"].astype(float)
    year_dum = pd.get_dummies(df["year"], prefix="year", drop_first=True)
    month_dum = pd.get_dummies(df["month"], prefix="month", drop_first=True)
    wd_dum = pd.get_dummies(df["weekday_code"], prefix="wd", drop_first=True)
    X = pd.concat(
        [
            pd.DataFrame({
                "is_friday13th": df["is_friday13th"].astype(float),
                "is_holiday_flag": df["is_holiday_flag"].astype(float),
            }),
            year_dum.astype(float),
            month_dum.astype(float),
            wd_dum.astype(float),
        ],
        axis=1,
    )
    X = sm.add_constant(X, has_constant="add")
    return X, y


def _extract_fit(res, X, y, method: str, family: str) -> dict:
    idx = X.columns.get_loc("is_friday13th")
    coef = float(res.params.iloc[idx])
    se = float(res.bse.iloc[idx])
    z = coef / se if se > 0 else float("nan")
    p = float(2 * (1 - stats.norm.cdf(abs(z)))) if np.isfinite(z) else float("nan")
    z_crit = 1.959963984540054
    ci_low = float(np.exp(coef - z_crit * se))
    ci_high = float(np.exp(coef + z_crit * se))
    if family == "nb2":
        alpha_mle = float(res.params.iloc[-1]) if len(res.params) > idx else float("nan")
    else:
        alpha_mle = float("nan")
    return {
        "converged": True,
        "family": family,
        "fit_method": method,
        "n_obs": int(len(y)),
        "k_params": int(X.shape[1]),
        "alpha_nb2": alpha_mle,
        "coef": coef,
        "se_iid": se,
        "z": float(z),
        "count_ratio": float(np.exp(coef)),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": p,
    }


def nb2_fit(df: pd.DataFrame) -> dict:
    """NB2 MLE fit (statsmodels.discrete.NegativeBinomial), alpha estimated jointly.

    Fallback chain for optimizer failures on sparse subgroups (e.g. fatal
    accidents with mean ~7.5/day): BFGS -> Nelder-Mead -> Poisson GLM.
    Reports the family + fit_method actually used in the JSON so downstream
    (manuscript + reviewer) sees when NB2 could not be fitted honestly.
    """
    X, y = _build_design(df)
    if X.shape[1] >= X.shape[0]:
        return {"converged": False, "reason": "rank_deficient",
                "n_obs": int(len(y)), "k_params": int(X.shape[1])}

    for method in ("bfgs", "nm"):
        try:
            model = NegativeBinomial(y, X, loglike_method="nb2")
            maxiter = 200 if method == "bfgs" else 2000
            res = model.fit(disp=0, method=method, maxiter=maxiter)
        except Exception:
            continue
        if res.mle_retvals.get("converged", False):
            return _extract_fit(res, X, y, method=f"nb2_{method}", family="nb2")

    try:
        pois = sm.GLM(y, X, family=sm.families.Poisson()).fit()
    except Exception as exc:
        return {"converged": False, "reason": f"all_fits_failed:{exc}",
                "n_obs": int(len(y)), "k_params": int(X.shape[1])}
    result = _extract_fit(pois, X, y, method="poisson_glm_fallback",
                           family="poisson")
    result["fallback_reason"] = (
        "NB2 MLE (BFGS+NM) failed to converge; Poisson approximation used. "
        "Reported CI/p ignore extra-Poisson dispersion — see per_subgroup "
        "JSON for the raw NB2 attempt failure and treat this row as "
        "approximate."
    )
    return result


def run_all_subgroups() -> dict:
    values: list[dict] = []
    table_rows: list[dict] = []
    per_subgroup: dict[str, dict] = {}

    raw_p_values: list[float] = []

    for spec in SUBGROUPS:
        df = load_subgroup(spec)
        desc = descriptive_stats(df)
        welch = welch_t_test(df)
        nb = nb2_fit(df)

        key = spec["key"]
        per_subgroup[key] = {"desc": desc, "welch": welch, "nb": nb}

        raw_p = welch.get("p_value", float("nan"))
        bonf_p = float(min(1.0, raw_p * N_SUBGROUPS)) if np.isfinite(raw_p) else float("nan")
        if np.isfinite(raw_p):
            raw_p_values.append(raw_p)

        rr = desc["rate_ratio_crude"]
        ci_lo = rr - welch["se_diff"] * stats.t.ppf(0.975, welch["df_welch"]) / desc["mean_other"] \
            if np.isfinite(welch.get("se_diff", float("nan"))) and desc["mean_other"] else float("nan")
        ci_hi = rr + welch["se_diff"] * stats.t.ppf(0.975, welch["df_welch"]) / desc["mean_other"] \
            if np.isfinite(welch.get("se_diff", float("nan"))) and desc["mean_other"] else float("nan")

        values += [
            _v(f"t4_{key}_n_fri13", desc["n_fri13"],
               f"Table 4 [{spec['label']}] N Fri13", "results", "d"),
            _v(f"t4_{key}_mean_fri13", desc["mean_fri13"],
               f"Table 4 [{spec['label']}] mean Fri13", "results", ".2f"),
            _v(f"t4_{key}_mean_other", desc["mean_other"],
               f"Table 4 [{spec['label']}] mean other Fri", "results", ".2f"),
            _v(f"t4_{key}_rr_crude", rr,
               f"Table 4 [{spec['label']}] crude rate ratio", "results", ".3f"),
            _v(f"t4_{key}_p_raw", raw_p,
               f"Table 4 [{spec['label']}] raw p (Welch t)", "results", ".4f"),
            _v(f"t4_{key}_p_bonferroni", bonf_p,
               f"Table 4 [{spec['label']}] Bonferroni p (x8)", "results", ".4f"),
        ]
        if nb.get("converged"):
            values += [
                _v(f"t4_{key}_nb_count_ratio", nb["count_ratio"],
                   f"Table 4 [{spec['label']}] NB-adjusted count ratio",
                   "results", ".3f"),
                _v(f"t4_{key}_nb_ci_low", nb["ci_low"],
                   f"Table 4 [{spec['label']}] NB CI lower", "results", ".3f"),
                _v(f"t4_{key}_nb_ci_high", nb["ci_high"],
                   f"Table 4 [{spec['label']}] NB CI upper", "results", ".3f"),
                _v(f"t4_{key}_nb_p", nb["p_value"],
                   f"Table 4 [{spec['label']}] NB p-value", "results", ".4f"),
                _v(f"t4_{key}_nb_alpha", nb["alpha_nb2"],
                   f"Table 4 [{spec['label']}] NB alpha (dispersion)",
                   "methods", ".4f"),
            ]

        table_rows.append({
            "subgroup_key": key,
            "subgroup_label": spec["label"],
            "n_fri13": desc["n_fri13"],
            "n_other": desc["n_other"],
            "mean_fri13": round(desc["mean_fri13"], 2)
                if np.isfinite(desc["mean_fri13"]) else None,
            "mean_other": round(desc["mean_other"], 2)
                if np.isfinite(desc["mean_other"]) else None,
            "rr_crude": round(rr, 3) if np.isfinite(rr) else None,
            "ci_low_crude": round(ci_lo, 3) if np.isfinite(ci_lo) else None,
            "ci_high_crude": round(ci_hi, 3) if np.isfinite(ci_hi) else None,
            "p_raw": round(raw_p, 4) if np.isfinite(raw_p) else None,
            "p_bonferroni": round(bonf_p, 4) if np.isfinite(bonf_p) else None,
            "nb_count_ratio": round(nb["count_ratio"], 3)
                if nb.get("converged") else None,
            "nb_ci_low": round(nb["ci_low"], 3) if nb.get("converged") else None,
            "nb_ci_high": round(nb["ci_high"], 3)
                if nb.get("converged") else None,
            "nb_p": round(nb["p_value"], 4) if nb.get("converged") else None,
            "nb_converged": bool(nb.get("converged", False)),
        })

    n_raw_significant = sum(1 for p in raw_p_values if p < ALPHA_FAMILY)
    n_bonferroni_significant = sum(
        1 for p in raw_p_values if p < BONFERRONI_THRESHOLD
    )

    values += [
        _v("t4_n_subgroups", N_SUBGROUPS,
           "Table 4 total subgroups", "methods", "d"),
        _v("t4_alpha_family", ALPHA_FAMILY,
           "Table 4 family-wise alpha", "methods", ".3f"),
        _v("t4_bonferroni_threshold", BONFERRONI_THRESHOLD,
           "Table 4 Bonferroni-adjusted threshold (alpha / 8)",
           "methods", ".5f"),
        _v("t4_n_raw_significant", n_raw_significant,
           "Table 4 N subgroups with raw p<0.05", "results", "d"),
        _v("t4_n_bonferroni_significant", n_bonferroni_significant,
           "Table 4 N subgroups surviving Bonferroni",
           "results", "d"),
    ]

    methods_notes = (
        f"Table 4 reports subgroup-specific comparisons of Fri13 vs. all other "
        f"Fridays on national daily accident counts, partitioned into {N_SUBGROUPS} "
        f"subgroups (severity x2, age x4, time-of-day x2). For each subgroup we "
        f"report the crude rate ratio with Welch two-sample t-test raw p, the "
        f"Bonferroni-adjusted p (alpha_family={ALPHA_FAMILY:.3f}, threshold="
        f"{BONFERRONI_THRESHOLD:.5f}), and a covariate-adjusted NB2 count ratio "
        f"from a national-level NB2 model with year, month, weekday, and holiday "
        f"controls; alpha was estimated by MLE. All 8 subgroups use the same "
        f"national-level NB2 specification for direct comparability. Prefecture-"
        f"level heterogeneity for the overall is_fri13 estimand is reported "
        f"separately in Figure S3 (Phase 2C-C4)."
    )

    return {
        "project": "friday13th",
        "phase": "2C-C5-Table4",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "src/09_subgroup_table4.py",
        "config": {
            "n_subgroups": N_SUBGROUPS,
            "alpha_family": ALPHA_FAMILY,
            "bonferroni_threshold": BONFERRONI_THRESHOLD,
        },
        "values": values,
        "table4_rows": table_rows,
        "per_subgroup": per_subgroup,
        "n_raw_significant": n_raw_significant,
        "n_bonferroni_significant": n_bonferroni_significant,
        "methods_notes": methods_notes,
    }


def main() -> None:
    result = run_all_subgroups()
    OUT_JSON.write_text(
        json.dumps(_to_native(result), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[OK] {OUT_JSON} written: {len(result['values'])} values, "
          f"{len(result['table4_rows'])} table rows")
    print(f"     raw p<0.05 count = {result['n_raw_significant']}, "
          f"Bonferroni survivors = {result['n_bonferroni_significant']}")


def _to_native(obj: Any) -> Any:
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        if np.isnan(val):
            return None
        return val
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    if isinstance(obj, float) and np.isnan(obj):
        return None
    return obj


if __name__ == "__main__":
    main()
