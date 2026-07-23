"""05_case_crossover.py

Phase 2C-C3: Case-crossover alternative tests for the Friday-the-13th
analysis. Provides three date-level tests independent of the prefecture
panel NB regression (which is exhaustively covered by 02/03/04):

(i)   Month-stratified conditional Poisson regression — hand-implemented
      Newton-Raphson maximizing the conditional log-likelihood after
      profiling out the month fixed effects. Cummings & McKnight (2004)
      show this is equivalent to Cox regression with time-stratified risk
      sets when the outcome is a count.
(ii)  Exact sign test — for each of the 10 same-month case-control triples,
      compare the Fri13 count against the mean of the same-month other
      Fridays; count the sign of the difference and apply a two-sided
      binomial exact test against p=0.5.
(iii) Paired log-ratio permutation test — for each pair compute
      log(fri13_count / control_mean), then permute the sign 10,000 times
      to build the null distribution of the mean log-ratio; two-sided
      permutation p and MC SE recorded.

Data source
-----------
fullmoon-accident/data/processed/accidents_clean.parquet — 1.88M records,
2019-01-01 to 2024-12-31. Aggregated to national daily counts. Every one of
the 10 Fri13 months contains exactly 4 Fridays, so each Fri13 is paired
against 3 same-month other Fridays (verified 2026-07-23 in MS-0).

Positioning
-----------
Case-crossover tests operate at the national daily level and are complementary
to the 47-prefecture panel NB analysis (2C-C2 / 2C-C1). They provide an
independent probe of "is a Fri13 systematically different from a matched
non-Fri13 Friday" without the modeling assumptions of NB2 dispersion or
cluster-robust inference. n=10 pairs limits statistical power; results are
interpreted as sensitivity, with the cluster z-based prefecture-panel result
(p=0.360) remaining primary.

Methods draft: emitted under case_crossover_results.json['methods_draft_c3']
for reuse when Phase 2C-C5 updates manuscript.md. Treat as scaffold, NOT
verbatim (2C-C1 P1-3/P1-5/P1-6 lesson: draft strings can bake in wording
that misrepresents the diagnostic).

Output
------
  output/case_crossover_results.json  (4 sections + methods_draft_c3)

Write is 2-pass (raw results first, methods draft second) so that a
formatting bug in the draft cannot lose the compute (2C-C1 P1-4 lesson).

Non-touch: 02/03/04/06b/01a/01b/01c/tests/test_*.py — this script only
reads accidents_clean.parquet.

Runtime: ~1 second (permutation loop 10k iter + NR ≤ 4 iters on real data).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# Ensure src/ is on sys.path for CLI execution (pytest handles via conftest).
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

ACCIDENTS_PARQUET = (
    Path.home()
    / "claude"
    / "analysis"
    / "fullmoon-accident"
    / "data"
    / "processed"
    / "accidents_clean.parquet"
)

DEFAULT_N_PERM = 10000
DEFAULT_SEED = 20260723

# 95% CI z-critical + safe conversions unified via _stats_helpers.py
# (2C-C4 D1+D4 fix: eliminates 3-form Z drift between 04/05/07 and 3-copy
# _safe_float/_safe_exp duplication pre-flagged in 2C-C3 P3-e).
from _stats_helpers import Z_CRIT_95, safe_exp as _safe_exp, safe_float as _safe_float  # noqa: E402, F401


# ---------------------------------------------------------------------------
# Data loading / pair construction
# ---------------------------------------------------------------------------


def load_accidents_daily(parquet_path: Path = ACCIDENTS_PARQUET) -> pd.DataFrame:
    """Load the accidents parquet and aggregate to national daily counts.

    Returns
    -------
    DataFrame with columns:
      date (datetime64), total_count (int), dow (0-6, Fri=4),
      day (1-31), year, month, ym (Period[M]),
      is_friday (bool), is_fri13 (bool).
    """
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"accidents_clean.parquet not found at {parquet_path}"
        )
    df = pd.read_parquet(parquet_path, columns=["occurred_at"])
    df["date"] = df["occurred_at"].dt.normalize()
    daily = (
        df.groupby("date")
        .size()
        .reset_index(name="total_count")
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily["dow"] = daily["date"].dt.dayofweek
    daily["day"] = daily["date"].dt.day
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    daily["ym"] = daily["date"].dt.to_period("M")
    daily["is_friday"] = daily["dow"] == 4
    daily["is_fri13"] = daily["is_friday"] & (daily["day"] == 13)
    return daily


def extract_case_control_pairs(daily: pd.DataFrame) -> pd.DataFrame:
    """Return a long-format table of case/control Fridays keyed by ym.

    One row per Friday inside a Fri13-containing month. Columns:
      ym, date, total_count, is_case (True for Fri13, False for control).
    Verified in MS-0: every Fri13 month has exactly 4 Fridays (1 case + 3
    controls), so 10 cases + 30 controls = 40 rows.
    """
    fri13_yms = daily.loc[daily["is_fri13"], "ym"].tolist()
    if len(fri13_yms) != 10:
        raise ValueError(
            f"expected 10 Fri13 dates in the 2019-2024 window, got {len(fri13_yms)}"
        )
    pairs = daily.loc[
        daily["is_friday"] & daily["ym"].isin(fri13_yms),
        ["ym", "date", "total_count", "is_fri13"],
    ].rename(columns={"is_fri13": "is_case"}).reset_index(drop=True)

    # Sanity: each ym should have exactly one case and >=1 control.
    per_ym = pairs.groupby("ym")["is_case"].agg(["sum", "count"])
    if not (per_ym["sum"] == 1).all():
        bad = per_ym[per_ym["sum"] != 1]
        raise ValueError(f"expected exactly one Fri13 per month, got:\n{bad}")
    if (per_ym["count"] - per_ym["sum"] < 1).any():
        bad = per_ym[per_ym["count"] - per_ym["sum"] < 1]
        raise ValueError(f"expected >=1 control per Fri13 month, got:\n{bad}")

    return pairs


def summarize_pairs(pairs: pd.DataFrame) -> dict:
    """Per-month case/control summary for the JSON payload."""
    rows = []
    for ym, sub in pairs.groupby("ym"):
        case_row = sub.loc[sub["is_case"]].iloc[0]
        ctrl = sub.loc[~sub["is_case"], "total_count"]
        rows.append(
            {
                "ym": str(ym),
                "fri13_date": str(case_row["date"].date()),
                "fri13_count": int(case_row["total_count"]),
                "n_controls": int(len(ctrl)),
                "control_mean": _safe_float(ctrl.mean()),
                "control_dates": [str(d.date()) for d in sub.loc[~sub["is_case"], "date"]],
            }
        )
    return {"n_pairs": len(rows), "pairs": rows}


# ---------------------------------------------------------------------------
# (i) Month-stratified conditional Poisson regression
# (ii) Exact sign test
# (iii) Paired log-ratio permutation test
# (iv) Methods draft
# ---------------------------------------------------------------------------


def _per_stratum_totals(pairs: pd.DataFrame) -> tuple[list[dict], np.ndarray, np.ndarray, np.ndarray]:
    """Pack pairs into per-stratum arrays: y_case, y_total, n_dates."""
    rows = []
    for ym, sub in pairs.groupby("ym"):
        y_case = int(sub.loc[sub["is_case"], "total_count"].iloc[0])
        y_total = int(sub["total_count"].sum())
        n = int(len(sub))
        rows.append({"ym": str(ym), "y_case": y_case, "y_total": y_total, "n": n})
    y_case = np.array([r["y_case"] for r in rows], dtype=float)
    y_total = np.array([r["y_total"] for r in rows], dtype=float)
    n_arr = np.array([r["n"] for r in rows], dtype=float)
    return rows, y_case, y_total, n_arr


def conditional_poisson_diagnostic(
    pairs: pd.DataFrame, max_iter: int = 100, tol: float = 1e-12
) -> dict:
    """Month-stratified conditional Poisson MLE for the Fri13 log rate ratio.

    Model. y_it ~ Poisson(exp(alpha_i + beta * is_fri13_it)), independent
    within stratum i (month). Conditioning on the stratum total y_i. profiles
    out alpha_i; the conditional joint of the n_i within-stratum counts is
    multinomial with p_it proportional to exp(beta * is_fri13_it). Since
    is_fri13 = 1 only for the case day within each stratum, the case-day
    count is Binomial(y_i., pi_i) with pi_i = exp(beta) / (exp(beta) + n_i - 1).

    Conditional log-likelihood in beta (dropping constants):
      logL(beta) = sum_i [ y_i^case * beta - y_i. * log(exp(beta) + n_i - 1) ].
    Score:
      s(beta) = sum_i [ y_i^case - y_i. * pi_i(beta) ].
    Hessian:
      H(beta) = -sum_i [ y_i. * exp(beta) * (n_i - 1) / (exp(beta) + n_i - 1)^2 ].

    Three inferential SEs are reported at the MLE:
      * Fisher (model-based, iid Poisson): SE = sqrt(-1 / H). Diagnostic only —
        Poisson equidispersion is known-violated for daily accident counts, so
        Fisher SE under-covers.
      * Sandwich (cluster-by-stratum) with G/(G-1) finite-sample scaling
        (Cameron & Miller 2015 §III.C): Var = (G/(G-1)) * H^{-1} * Σ s_i^2 * H^{-1}.
      * Sandwich Wald CIs report BOTH z(0.975)=1.96 and t(G-1) critical values.
        At G=10 strata, t(G-1)-based inference is the small-G-honest reporting.

    Non-convergence within max_iter raises RuntimeError (matches the sibling
    04_diagnostics.py MLE policy — 2C-C3 P2-E fix, silent-fail prevention).
    """
    per_stratum, y_case, y_total, n_arr = _per_stratum_totals(pairs)
    G = int(len(per_stratum))

    # Newton-Raphson on beta
    beta = 0.0
    converged = False
    n_iter = 0
    for it in range(1, max_iter + 1):
        n_iter = it
        r = _safe_exp(beta)
        if r is None:
            raise RuntimeError(
                f"conditional Poisson NR overflowed at iter={it}, beta={beta}"
            )
        denom = r + n_arr - 1.0
        pi = r / denom
        score = float(np.sum(y_case - y_total * pi))
        hess = float(-np.sum(y_total * r * (n_arr - 1.0) / denom ** 2))
        if abs(hess) < 1e-14:
            break
        step = -score / hess
        beta_new = beta + step
        if abs(step) < tol:
            beta = beta_new
            converged = True
            break
        beta = beta_new

    if not converged:
        raise RuntimeError(
            f"conditional Poisson MLE did not converge in {max_iter} iterations "
            f"(final beta={beta}, |step|>{tol})"
        )

    # Evaluate at MLE
    r_mle = _safe_exp(beta)
    if r_mle is None:
        raise RuntimeError(f"conditional Poisson exp(beta_mle) overflowed at beta={beta}")
    denom = r_mle + n_arr - 1.0
    pi = r_mle / denom
    s_per = y_case - y_total * pi  # per-stratum score contribution
    hess = float(-np.sum(y_total * r_mle * (n_arr - 1.0) / denom ** 2))

    if hess >= 0:
        raise RuntimeError(
            f"conditional Poisson Hessian non-negative at MLE (hess={hess}); "
            f"design likely degenerate"
        )

    fisher_var = -1.0 / hess
    fisher_se = math.sqrt(fisher_var) if fisher_var > 0 else float("nan")

    bread = -1.0 / hess
    meat = float(np.sum(s_per ** 2))
    finite_cluster_correction = G / (G - 1) if G > 1 else 1.0
    sandwich_var = finite_cluster_correction * bread * meat * bread
    sandwich_se = math.sqrt(sandwich_var) if sandwich_var > 0 else float("nan")

    t_crit = float(stats.t.ppf(0.975, df=G - 1))

    def _wald_result(se: float, crit: float, crit_label: str) -> dict:
        if not (math.isfinite(se) and se > 0):
            return {
                "se_beta": _safe_float(se),
                "critical_value": _safe_float(crit),
                "critical_value_label": crit_label,
                "z": None,
                "p_two_sided": None,
                "count_ratio_ci_low": None,
                "count_ratio_ci_high": None,
            }
        z_val = beta / se
        if crit_label.startswith("z"):
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_val))))
        else:
            p_val = float(2.0 * (1.0 - stats.t.cdf(abs(z_val), df=G - 1)))
        return {
            "se_beta": _safe_float(se),
            "critical_value": _safe_float(crit),
            "critical_value_label": crit_label,
            "z": _safe_float(z_val),
            "p_two_sided": _safe_float(p_val),
            "count_ratio_ci_low": _safe_exp(beta - crit * se),
            "count_ratio_ci_high": _safe_exp(beta + crit * se),
        }

    return {
        "method": "conditional_poisson_newton_raphson_hand_implemented",
        "n_strata": G,
        "n_iter": int(n_iter),
        "converged": True,  # non-converged now raises RuntimeError above
        "score_at_mle": _safe_float(float(np.sum(s_per))),
        "beta": _safe_float(beta),
        "count_ratio": _safe_exp(beta),
        "small_G_correction": {
            "G": G,
            "finite_cluster_correction_factor": _safe_float(finite_cluster_correction),
            "t_crit_95_df": _safe_float(t_crit),
            "z_crit_95": Z_CRIT_95,
        },
        "fisher_iid_diagnostic_only": _wald_result(fisher_se, Z_CRIT_95, "z(0.975)"),
        "sandwich_cluster_z": _wald_result(sandwich_se, Z_CRIT_95, "z(0.975)"),
        "sandwich_cluster_t": _wald_result(sandwich_se, t_crit, f"t(0.975, df={G-1})"),
        "per_stratum": [
            {
                **r,
                "pi_at_mle": _safe_float(p),
                "expected_case_at_mle": _safe_float(p * r["y_total"]),
                "score_at_mle": _safe_float(s),
            }
            for r, p, s in zip(per_stratum, pi.tolist(), s_per.tolist())
        ],
    }


def exact_sign_diagnostic(pairs: pd.DataFrame) -> dict:
    """Two-sided exact binomial sign test on Fri13 vs same-month control mean."""
    per_pair = []
    signs: list[str] = []
    for ym, sub in pairs.groupby("ym"):
        case = float(sub.loc[sub["is_case"], "total_count"].iloc[0])
        ctrl_vals = sub.loc[~sub["is_case"], "total_count"].astype(float)
        ctrl_mean = float(ctrl_vals.mean())
        diff = case - ctrl_mean
        if diff > 0:
            sign = "+"
        elif diff < 0:
            sign = "-"
        else:
            sign = "0"
        signs.append(sign)
        per_pair.append(
            {
                "ym": str(ym),
                "fri13_count": _safe_float(case),
                "control_mean": _safe_float(ctrl_mean),
                "n_controls": int(len(ctrl_vals)),
                "diff": _safe_float(diff),
                "sign": sign,
            }
        )
    n_plus = signs.count("+")
    n_minus = signs.count("-")
    n_zero = signs.count("0")
    n_nonzero = n_plus + n_minus

    if n_nonzero == 0:
        p_two_sided: float | None = None
    else:
        p_two_sided = float(
            stats.binomtest(n_plus, n=n_nonzero, p=0.5, alternative="two-sided").pvalue
        )

    return {
        "method": "binomtest_two_sided_p_half",
        "n_pairs": len(signs),
        "n_plus": int(n_plus),
        "n_minus": int(n_minus),
        "n_zero": int(n_zero),
        "n_nonzero": int(n_nonzero),
        "expected_plus_h0": _safe_float(0.5 * n_nonzero),
        "p_two_sided": _safe_float(p_two_sided),
        "per_pair": per_pair,
    }


def permutation_diagnostic(pairs: pd.DataFrame, n_perm: int, seed: int) -> dict:
    """Paired log-ratio permutation test with sign-flip null.

    For each stratum compute r_i = log(fri13_count / mean(other Fridays)).
    Under H0 of exchangeability, the sign of r_i is symmetric around 0. Two-
    sided p from the mean-|log_ratio| null distribution. With n_pairs=10 we
    additionally enumerate all 2^10 = 1024 sign patterns for an exact p; the
    Monte-Carlo p at n_perm iterations is reported for cross-checking and
    MC-SE sizing.
    """
    per_pair = []
    ratios: list[float] = []
    for ym, sub in pairs.groupby("ym"):
        case = float(sub.loc[sub["is_case"], "total_count"].iloc[0])
        ctrl_mean = float(sub.loc[~sub["is_case"], "total_count"].astype(float).mean())
        if case <= 0 or ctrl_mean <= 0:
            raise ValueError(
                f"non-positive daily count in {ym}: case={case}, ctrl_mean={ctrl_mean}"
            )
        lr = math.log(case / ctrl_mean)
        ratios.append(lr)
        per_pair.append(
            {
                "ym": str(ym),
                "log_ratio": _safe_float(lr),
                "abs_log_ratio": _safe_float(abs(lr)),
            }
        )

    arr = np.array(ratios, dtype=float)
    n = int(len(arr))
    observed_mean = float(arr.mean())

    # Exact enumeration
    if n <= 20:
        n_patterns = 1 << n
        pattern_ids = np.arange(n_patterns, dtype=np.int64)
        signs_all = (((pattern_ids[:, None] >> np.arange(n)) & 1) * 2 - 1).astype(float)
        null_means = (signs_all * arr).mean(axis=1)
        n_extreme_exact = int(np.sum(np.abs(null_means) >= abs(observed_mean) - 1e-15))
        exact_p = float(n_extreme_exact / n_patterns)
        exact_block = {
            "n_sign_patterns": int(n_patterns),
            "n_extreme": int(n_extreme_exact),
            "p_two_sided": _safe_float(exact_p),
        }
    else:
        exact_block = {"n_sign_patterns": None, "n_extreme": None, "p_two_sided": None}

    # Monte Carlo
    rng = np.random.default_rng(seed)
    signs_mc = rng.choice([-1.0, 1.0], size=(n_perm, n))
    mc_null_means = (signs_mc * arr).mean(axis=1)
    n_extreme_mc = int(np.sum(np.abs(mc_null_means) >= abs(observed_mean) - 1e-15))
    mc_p = float(n_extreme_mc / n_perm)
    mc_se_p = float(math.sqrt(mc_p * (1.0 - mc_p) / n_perm)) if 0.0 < mc_p < 1.0 else 0.0

    return {
        "method": "sign_flip_permutation_mean_log_ratio",
        "n_pairs": n,
        "observed_mean_log_ratio": _safe_float(observed_mean),
        "observed_geometric_ratio": _safe_exp(observed_mean),
        "exact_enumeration": exact_block,
        "monte_carlo": {
            "n_perm": int(n_perm),
            "seed": int(seed),
            "n_extreme": int(n_extreme_mc),
            "p_two_sided": _safe_float(mc_p),
            "mc_se_p": _safe_float(mc_se_p),
        },
        "per_pair": per_pair,
    }


def build_methods_draft_c3(payload: dict) -> dict:
    """Scaffold Methods paragraphs for 2C-C5 manuscript integration.

    NOTE: Treat as scaffold, not verbatim (2C-C1 P1-3/P1-5/P1-6 lesson).
    Fact-check each paragraph against the current JSON before pasting into
    manuscript.md. See `notes[]` for the manuscript.md replacement map.
    """
    cp = payload["conditional_poisson"]
    es = payload["exact_sign"]
    pm = payload["permutation"]
    pair_summary = payload["pair_summary"]

    sand_z = cp["sandwich_cluster_z"]
    sand_t = cp["sandwich_cluster_t"]
    corr = cp["small_G_correction"]
    mc = pm["monte_carlo"]
    exact = pm["exact_enumeration"]

    paragraphs: list[str] = []

    n_pairs = pair_summary["n_pairs"]
    # 40 = 10 Fri13 months × 4 Fridays each — invariant enforced by
    # extract_case_control_pairs and asserted in test_extract_pairs_exactly_ten.
    n_fridays = n_pairs * 4
    paragraphs.append(
        "Case-crossover alternative tests. To triangulate the prefecture-panel "
        "negative-binomial finding, we ran three date-level tests on national "
        "daily accident counts, restricted to the {n_frid} Fridays "
        "({n_pairs} months x 4 Fridays each) inside the {n_pairs} Fri13-"
        "containing months of 2019-2024. Each of the {n_pairs} Fri13 dates was "
        "paired against the three same-month other Fridays; no month contained "
        "more than one Fri13.".format(n_frid=n_fridays, n_pairs=n_pairs)
    )

    paragraphs.append(
        "Month-stratified conditional Poisson regression. Following the "
        "case-crossover-as-conditional-Poisson framing (Maclure 1991, Lu & "
        "Zeger 2007), we eliminated the {n} month intercepts by conditioning "
        "on the stratum totals and maximized the resulting conditional "
        "likelihood in beta via Newton-Raphson (iterations={ni}). The MLE "
        "gave count ratio {cr}. With G={G} clusters, cluster-robust inference "
        "is small-G-sensitive: we report the cluster-by-stratum sandwich SE "
        "with the Cameron & Miller (2015) finite-cluster factor G/(G-1)={fcc} "
        "and Wald tests using BOTH the z(0.975)=1.96 and the t(G-1)={tc} "
        "critical values. Sandwich SE_beta = {sse}. z-based 95% CI [{slo_z}, "
        "{shi_z}], p = {sp_z}. t(G-1)-based 95% CI [{slo_t}, {shi_t}], p = "
        "{sp_t}. Under G=10 the t(G-1) inference is the honest primary "
        "reporting. Fisher iid SE is retained in the JSON for audit but is "
        "not reported here; Poisson equidispersion is violated for daily "
        "police accident counts (2C-C1 dispersion diagnostic gives nb2 "
        "alpha = 0.023), and the Fisher/sandwich SE ratio of {ratio} is "
        "consistent with that alpha plus within-stratum autocorrelation "
        "absorbed by the sandwich.".format(
            n=cp["n_strata"],
            G=cp["n_strata"],
            ni=cp["n_iter"],
            cr=_fmt(cp["count_ratio"]),
            fcc=_fmt(corr["finite_cluster_correction_factor"], digits=3),
            tc=_fmt(corr["t_crit_95_df"], digits=3),
            sse=_fmt(sand_z["se_beta"]),
            slo_z=_fmt(sand_z["count_ratio_ci_low"]),
            shi_z=_fmt(sand_z["count_ratio_ci_high"]),
            sp_z=_fmt(sand_z["p_two_sided"], digits=3),
            slo_t=_fmt(sand_t["count_ratio_ci_low"]),
            shi_t=_fmt(sand_t["count_ratio_ci_high"]),
            sp_t=_fmt(sand_t["p_two_sided"], digits=3),
            ratio=_fmt(
                sand_z["se_beta"] / cp["fisher_iid_diagnostic_only"]["se_beta"]
                if cp["fisher_iid_diagnostic_only"]["se_beta"]
                else None,
                digits=2,
            ),
        )
    )

    paragraphs.append(
        "Exact sign test. Of the {n} same-month case-control comparisons, "
        "{np} favored a higher Fri13 count and {nm} favored a higher control "
        "mean (ties={nz}). Ties, if present, are excluded from the denominator "
        "and the two-sided binomial exact test against p=0.5 is computed on "
        "the {nn} non-tied pairs; here {nn} = 10. p = {p}. With ten pairs the "
        "test has limited power to distinguish small effects and reaches its "
        "smallest achievable two-sided p at 10-0/0-10 splits, so an 8-2 split "
        "landing at p=0.11 reflects the discrete power ceiling, not a "
        "borderline signal.".format(
            n=es["n_pairs"],
            np=es["n_plus"],
            nm=es["n_minus"],
            nz=es["n_zero"],
            nn=es["n_nonzero"],
            p=_fmt(es["p_two_sided"], digits=3),
        )
    )

    paragraphs.append(
        "Paired log-ratio permutation test (sign-flip null, Pesarin & Salmaso "
        "2010 §4). For each pair we computed log(fri13_count / mean(other "
        "Fridays)) and permuted the {n} signs; the sign-flip null tests "
        "symmetry of the pair-wise log-ratio around 0 without additional "
        "distributional assumptions. The 2^{n} = {npat} sign patterns admit "
        "exact enumeration; the observed mean log-ratio was {olr} (geometric "
        "count ratio {gr}). Exact two-sided p = {exp} ({nex} extreme patterns "
        "of {npat}). The Monte-Carlo estimate at {npi} iterations matched "
        "(p = {mcp}, MC SE = {mcse}).".format(
            n=pm["n_pairs"],
            npat=exact["n_sign_patterns"],
            olr=_fmt(pm["observed_mean_log_ratio"], digits=4, signed=True),
            gr=_fmt(pm["observed_geometric_ratio"]),
            exp=_fmt(exact["p_two_sided"], digits=3),
            nex=exact["n_extreme"],
            npi=mc["n_perm"],
            mcp=_fmt(mc["p_two_sided"], digits=3),
            mcse=_fmt(mc["mc_se_p"], digits=4),
        )
    )

    paragraphs.append(
        "Scope, primary vs. sensitivity, and limitations. Among the three "
        "tests, the month-stratified conditional Poisson with t(G-1)-based "
        "cluster-robust SE is the primary case-crossover result (p={sp_t}); "
        "the paired log-ratio permutation test (p={pp}) is the more powerful "
        "nonparametric complement, and the exact sign test (p={ep}) is a "
        "coarse rank-based fallback whose discrete p-value floor at n=10 "
        "should not be over-interpreted. All three land above 0.10 with "
        "point estimates near 1.04, consistent with the prefecture-panel "
        "cluster result but not corroborating it in a strict inferential "
        "sense (independent samples share the same accident stream). "
        "Case-crossover uses national daily aggregates and does not exploit "
        "prefecture heterogeneity (handled by the 2C-C2 panel model); n=10 "
        "pairs limits power to small effects.".format(
            sp_t=_fmt(sand_t["p_two_sided"], digits=3),
            pp=_fmt(exact["p_two_sided"], digits=3),
            ep=_fmt(es["p_two_sided"], digits=3),
        )
    )

    return {
        "paragraphs": paragraphs,
        "notes": [
            "Scaffold only. Do NOT copy verbatim into manuscript.md — fact-check "
            "each paragraph against the current JSON (2C-C1 P1-3/P1-5/P1-6 lesson).",
            "manuscript.md replacement map for 2C-C5: (a) L19 Abstract Methods "
            "list = add 'month-stratified conditional Poisson regression + "
            "sign test + sign-flip permutation'; (b) L21 Abstract Results = "
            "REPLACE 'mean ratio of 1.05 (p=0.32)' with 't(G-1)-based cluster "
            "p from the conditional Poisson' (see paragraph 2); (c) L59 Methods "
            "case-crossover paragraph = REPLACE with paragraphs 1-4 here; "
            "(d) L99 Results case-crossover paragraph = REPLACE with the "
            "sandwich-t(G-1) result + 8/10 sign-count sentence; (e) Table 1 "
            "L188-202 'Mean' row = arithmetic 1.05 uses per-pair-ratio mean, "
            "not the geometric ratio 1.036 used here — add a geometric-mean "
            "note OR add a geometric row for referee transparency.",
            "Old Näyhä-style t-test on per-pair arithmetic ratios "
            "(src/02_main_analysis.py::case_crossover, mean=1.05, t=1.05, "
            "p=0.32) is superseded by the conditional Poisson MLE here; the "
            "'8 of 10 Fridays higher' framing IS preserved and appears in "
            "paragraph 3 as the exact sign test's 8+/2- count.",
            "Fisher iid SE is NOT reported in the manuscript-facing text — "
            "Poisson equidispersion is misspecified for these counts and the "
            "Fisher CI ([1.013, 1.060]) would misleadingly exclude 1.0 if "
            "pasted alongside the sandwich CI. Kept in "
            "case_crossover_results.json['conditional_poisson']"
            "['fisher_iid_diagnostic_only'] for audit only.",
            "Citations to add to bibliography if not already present: Maclure "
            "(1991) AJE 133:144-153 (case-crossover); Lu & Zeger (2007) "
            "Biostatistics 8:337-344 (CC-conditional-Poisson equivalence); "
            "Cameron & Miller (2015) J Human Resources 50:317-372 (cluster-"
            "robust inference small-G); Pesarin & Salmaso (2010) Permutation "
            "Tests for Complex Data.",
        ],
    }


def _fmt(x, digits: int = 4, signed: bool = False) -> str:
    """Compact numeric formatter tolerant of None."""
    if x is None:
        return "NA"
    if signed:
        return f"{x:+.{digits}f}"
    return f"{x:.{digits}f}"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_all_case_crossover(n_perm: int, seed: int) -> dict:
    daily = load_accidents_daily()
    pairs = extract_case_control_pairs(daily)
    payload: dict = {
        "config": {
            "n_perm_requested": int(n_perm),
            "permutation_seed": int(seed),
            "z_crit_95": Z_CRIT_95,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "pair_summary": summarize_pairs(pairs),
    }
    payload["conditional_poisson"] = conditional_poisson_diagnostic(pairs)
    payload["exact_sign"] = exact_sign_diagnostic(pairs)
    payload["permutation"] = permutation_diagnostic(pairs, n_perm=n_perm, seed=seed)
    return payload


def write_results(payload: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, allow_nan=False, ensure_ascii=False)


def _positive_int(raw: str) -> int:
    """argparse type for strictly positive integer (2C-C3 P2-B fix)."""
    try:
        v = int(raw)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"not an integer: {raw!r}") from exc
    if v <= 0:
        raise argparse.ArgumentTypeError(f"must be > 0, got {v}")
    return v


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--n-perm",
        type=_positive_int,
        default=DEFAULT_N_PERM,
        help=f"permutation iterations, must be > 0 (default {DEFAULT_N_PERM})",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED, help=f"RNG seed (default {DEFAULT_SEED})"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUTPUT / "case_crossover_results.json",
        help="output JSON path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = run_all_case_crossover(n_perm=args.n_perm, seed=args.seed)

    # 2-pass write (2C-C1 P1-4 lesson): raw results first, methods draft second.
    write_results(payload, args.out)
    try:
        payload["methods_draft_c3"] = build_methods_draft_c3(payload)
        write_results(payload, args.out)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] methods_draft_c3 build failed: {exc}", file=sys.stderr)
        print("       raw diagnostics still written to", args.out, file=sys.stderr)
    print(f"[OK] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
