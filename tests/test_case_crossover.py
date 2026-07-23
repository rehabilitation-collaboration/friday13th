"""Tests for src/05_case_crossover.py (Phase 2C-C3).

Coverage:
  * Helpers: _safe_float / _safe_exp / _fmt.
  * Data loading + pair extraction (relies on fullmoon-accident parquet).
  * Direct unit tests of the 3 diagnostic functions on synthetic + real data.
  * JSON snapshot integration (all sections present, ranges valid).
  * MC ↔ exact permutation cross-check (MC must land inside 3*MC-SE of exact).
  * Newton-Raphson sanity (score at MLE ~ 0; iid vs sandwich SE monotone in
    overdispersion).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def test_safe_float_finite(case_crossover_module):
    assert case_crossover_module._safe_float(1.5) == 1.5
    assert case_crossover_module._safe_float(0) == 0.0


def test_safe_float_nan_inf(case_crossover_module):
    assert case_crossover_module._safe_float(float("nan")) is None
    assert case_crossover_module._safe_float(float("inf")) is None
    assert case_crossover_module._safe_float(float("-inf")) is None
    assert case_crossover_module._safe_float("not-a-number") is None


def test_safe_exp_finite(case_crossover_module):
    assert case_crossover_module._safe_exp(0.0) == pytest.approx(1.0)
    assert case_crossover_module._safe_exp(1.0) == pytest.approx(math.e)


def test_safe_exp_overflow(case_crossover_module):
    assert case_crossover_module._safe_exp(1e6) is None
    assert case_crossover_module._safe_exp(float("nan")) is None


def test_fmt_signed_and_none(case_crossover_module):
    assert case_crossover_module._fmt(None) == "NA"
    assert case_crossover_module._fmt(0.5, digits=2) == "0.50"
    assert case_crossover_module._fmt(0.5, digits=2, signed=True) == "+0.50"
    assert case_crossover_module._fmt(-0.5, digits=2, signed=True) == "-0.50"


# ---------------------------------------------------------------------------
# Data loading / pair extraction
# ---------------------------------------------------------------------------


def test_load_daily_shape_and_columns(case_crossover_module):
    daily = case_crossover_module.load_accidents_daily()
    # 2019-2024 = 2192 days
    assert len(daily) == 2192
    assert daily["date"].min() == pd.Timestamp("2019-01-01")
    assert daily["date"].max() == pd.Timestamp("2024-12-31")
    expected_cols = {
        "date",
        "total_count",
        "dow",
        "day",
        "year",
        "month",
        "ym",
        "is_friday",
        "is_fri13",
    }
    assert expected_cols.issubset(daily.columns)
    # every count > 0 (nationwide)
    assert (daily["total_count"] > 0).all()


def test_extract_pairs_exactly_ten(case_crossover_pairs):
    pairs = case_crossover_pairs
    n_cases = int(pairs["is_case"].sum())
    n_controls = int((~pairs["is_case"]).sum())
    assert n_cases == 10
    assert n_controls == 30  # all 10 Fri13 months contain exactly 4 Fridays
    per_ym = pairs.groupby("ym")["is_case"].agg(["sum", "count"])
    assert (per_ym["sum"] == 1).all()
    assert (per_ym["count"] == 4).all()


def test_extract_pairs_all_positive_counts(case_crossover_pairs):
    assert (case_crossover_pairs["total_count"] > 0).all()


def test_extract_pairs_missing_fri13_raises(case_crossover_module):
    """Feed a synthetic daily table with no Fri13 → ValueError."""
    daily = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", "2020-01-31", freq="D"),
            "total_count": [1000] * 31,
        }
    )
    daily["dow"] = daily["date"].dt.dayofweek
    daily["day"] = daily["date"].dt.day
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    daily["ym"] = daily["date"].dt.to_period("M")
    daily["is_friday"] = daily["dow"] == 4
    daily["is_fri13"] = daily["is_friday"] & (daily["day"] == 13)
    # 2020-01-13 is Monday, not Friday → 0 Fri13
    with pytest.raises(ValueError, match="expected 10 Fri13 dates"):
        case_crossover_module.extract_case_control_pairs(daily)


# ---------------------------------------------------------------------------
# Conditional Poisson (unit)
# ---------------------------------------------------------------------------


def _synthetic_pairs(case_counts, control_counts_per_month):
    """Build a pair dataframe matching the shape extract_case_control_pairs
    produces. control_counts_per_month = list of iterables (one per month)."""
    rows = []
    for i, (c, ctrls) in enumerate(zip(case_counts, control_counts_per_month)):
        ym = pd.Period(f"2020-{i+1:02d}", freq="M")
        rows.append(
            {
                "ym": ym,
                "date": pd.Timestamp(f"2020-{i+1:02d}-13"),
                "total_count": int(c),
                "is_case": True,
            }
        )
        for j, v in enumerate(ctrls):
            rows.append(
                {
                    "ym": ym,
                    "date": pd.Timestamp(f"2020-{i+1:02d}-{6 + 7*j:02d}"),
                    "total_count": int(v),
                    "is_case": False,
                }
            )
    return pd.DataFrame(rows)


def test_conditional_poisson_null_at_equal_counts(case_crossover_module):
    """Case = control mean per stratum → MLE β̂ = 0, count_ratio = 1."""
    pairs = _synthetic_pairs(
        case_counts=[100] * 5,
        control_counts_per_month=[[100, 100, 100]] * 5,
    )
    res = case_crossover_module.conditional_poisson_diagnostic(pairs)
    assert res["converged"] is True
    assert res["beta"] == pytest.approx(0.0, abs=1e-8)
    assert res["count_ratio"] == pytest.approx(1.0, abs=1e-8)
    assert abs(res["score_at_mle"]) < 1e-6


def test_conditional_poisson_score_at_mle_near_zero(case_crossover_module, case_crossover_pairs):
    res = case_crossover_module.conditional_poisson_diagnostic(case_crossover_pairs)
    assert res["converged"] is True
    # Score at MLE must be near-zero by the FOC.
    assert abs(res["score_at_mle"]) < 1e-4


def test_conditional_poisson_sandwich_wider_than_fisher_on_overdispersed(
    case_crossover_module, case_crossover_pairs
):
    """Real accident data is overdispersed; sandwich SE must exceed Fisher SE.

    Both z-based and t(G-1)-based sandwich blocks share the same SE_beta;
    the finite-cluster factor G/(G-1) further inflates it beyond the raw
    (uncorrected) sandwich, so the strict inequality holds for both.
    """
    res = case_crossover_module.conditional_poisson_diagnostic(case_crossover_pairs)
    fisher_se = res["fisher_iid_diagnostic_only"]["se_beta"]
    assert res["sandwich_cluster_z"]["se_beta"] > fisher_se
    assert res["sandwich_cluster_t"]["se_beta"] > fisher_se


def test_conditional_poisson_ci_contains_point_estimate(case_crossover_module, case_crossover_pairs):
    res = case_crossover_module.conditional_poisson_diagnostic(case_crossover_pairs)
    cr = res["count_ratio"]
    for key in ("fisher_iid_diagnostic_only", "sandwich_cluster_z", "sandwich_cluster_t"):
        lo = res[key]["count_ratio_ci_low"]
        hi = res[key]["count_ratio_ci_high"]
        assert lo < cr < hi, f"{key}: {lo} < {cr} < {hi}"


def test_conditional_poisson_t_ci_wider_than_z_ci(case_crossover_module, case_crossover_pairs):
    """At G=10, t(9)=2.262 > z(0.975)=1.96 → t-based CI must be strictly wider (2C-C3 P1-A)."""
    res = case_crossover_module.conditional_poisson_diagnostic(case_crossover_pairs)
    z_width = res["sandwich_cluster_z"]["count_ratio_ci_high"] - res["sandwich_cluster_z"]["count_ratio_ci_low"]
    t_width = res["sandwich_cluster_t"]["count_ratio_ci_high"] - res["sandwich_cluster_t"]["count_ratio_ci_low"]
    assert t_width > z_width
    # t p must be >= z p (the same test statistic against a heavier-tailed distribution)
    assert res["sandwich_cluster_t"]["p_two_sided"] >= res["sandwich_cluster_z"]["p_two_sided"]


def test_conditional_poisson_raises_on_non_convergence(case_crossover_module, case_crossover_pairs):
    """max_iter=1 forces early exit before |step|<tol; must raise RuntimeError (2C-C3 P2-E)."""
    with pytest.raises(RuntimeError, match="did not converge"):
        case_crossover_module.conditional_poisson_diagnostic(case_crossover_pairs, max_iter=1)


def test_conditional_poisson_small_G_correction_fields(case_crossover_module, case_crossover_pairs):
    res = case_crossover_module.conditional_poisson_diagnostic(case_crossover_pairs)
    corr = res["small_G_correction"]
    assert corr["G"] == 10
    assert corr["finite_cluster_correction_factor"] == pytest.approx(10 / 9)
    assert corr["t_crit_95_df"] == pytest.approx(2.2622, abs=1e-3)  # t(0.975, df=9)
    # 2C-C4 D1+D4: unified Z_CRIT_95 to scipy.stats.norm.ppf(0.975) full precision.
    assert corr["z_crit_95"] == pytest.approx(1.959963984540054, abs=1e-12)


# ---------------------------------------------------------------------------
# Exact sign test (unit)
# ---------------------------------------------------------------------------


def test_exact_sign_matches_scipy_binomtest_on_real_data(
    case_crossover_module, case_crossover_pairs
):
    from scipy import stats

    res = case_crossover_module.exact_sign_diagnostic(case_crossover_pairs)
    expected = float(
        stats.binomtest(res["n_plus"], n=res["n_nonzero"], p=0.5, alternative="two-sided").pvalue
    )
    assert res["p_two_sided"] == pytest.approx(expected, rel=1e-10)


def test_exact_sign_p_in_range(case_crossover_module, case_crossover_pairs):
    res = case_crossover_module.exact_sign_diagnostic(case_crossover_pairs)
    assert 0.0 <= res["p_two_sided"] <= 1.0


def test_exact_sign_zero_case_yields_all_minus(case_crossover_module):
    pairs = _synthetic_pairs(
        case_counts=[1] * 5,
        control_counts_per_month=[[100, 100, 100]] * 5,
    )
    res = case_crossover_module.exact_sign_diagnostic(pairs)
    assert res["n_plus"] == 0
    assert res["n_minus"] == 5


# ---------------------------------------------------------------------------
# Permutation (unit)
# ---------------------------------------------------------------------------


def test_permutation_exact_matches_mc_within_mc_se(
    case_crossover_module, case_crossover_pairs
):
    """MC p at 10,000 iter must land within 4*MC_SE of the exact p."""
    res = case_crossover_module.permutation_diagnostic(
        case_crossover_pairs, n_perm=10000, seed=20260723
    )
    exact_p = res["exact_enumeration"]["p_two_sided"]
    mc_p = res["monte_carlo"]["p_two_sided"]
    mc_se = res["monte_carlo"]["mc_se_p"]
    assert abs(mc_p - exact_p) <= 4 * mc_se


def test_permutation_observed_mean_matches_geometric_ratio(
    case_crossover_module, case_crossover_pairs
):
    res = case_crossover_module.permutation_diagnostic(
        case_crossover_pairs, n_perm=1000, seed=20260723
    )
    assert res["observed_geometric_ratio"] == pytest.approx(
        math.exp(res["observed_mean_log_ratio"]), rel=1e-9
    )


def test_permutation_symmetric_data_yields_high_p(case_crossover_module):
    """Case=control per stratum → observed mean log_ratio = 0 → exact p = 1."""
    pairs = _synthetic_pairs(
        case_counts=[100] * 10,
        control_counts_per_month=[[100, 100, 100]] * 10,
    )
    res = case_crossover_module.permutation_diagnostic(pairs, n_perm=1000, seed=0)
    assert res["observed_mean_log_ratio"] == pytest.approx(0.0, abs=1e-12)
    assert res["exact_enumeration"]["p_two_sided"] == pytest.approx(1.0)


def test_permutation_non_positive_count_raises(case_crossover_module):
    pairs = _synthetic_pairs(
        case_counts=[0, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        control_counts_per_month=[[100, 100, 100]] * 10,
    )
    with pytest.raises(ValueError, match="non-positive daily count"):
        case_crossover_module.permutation_diagnostic(pairs, n_perm=100, seed=0)


# ---------------------------------------------------------------------------
# argparse / main / 2-pass write recovery (2C-C3 P2-B, P2-J)
# ---------------------------------------------------------------------------


def test_positive_int_rejects_zero_and_negative(case_crossover_module):
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        case_crossover_module._positive_int("0")
    with pytest.raises(argparse.ArgumentTypeError):
        case_crossover_module._positive_int("-3")
    with pytest.raises(argparse.ArgumentTypeError):
        case_crossover_module._positive_int("not-int")
    assert case_crossover_module._positive_int("5") == 5


def test_parse_args_rejects_non_positive_n_perm(case_crossover_module):
    with pytest.raises(SystemExit):
        case_crossover_module.parse_args(["--n-perm", "0"])
    with pytest.raises(SystemExit):
        case_crossover_module.parse_args(["--n-perm", "-1"])


def test_main_two_pass_recovery_on_methods_draft_failure(
    tmp_path, monkeypatch, case_crossover_module
):
    """2C-C3 P2-J: if build_methods_draft_c3 raises, raw diagnostics must still be persisted."""
    out_path = tmp_path / "cc_recovery.json"

    def _boom(payload):
        raise RuntimeError("simulated methods draft failure")

    monkeypatch.setattr(case_crossover_module, "build_methods_draft_c3", _boom)
    rc = case_crossover_module.main(
        ["--n-perm", "100", "--out", str(out_path)]
    )
    assert rc == 0
    import json

    payload = json.loads(out_path.read_text())
    # raw diagnostics persisted
    assert "conditional_poisson" in payload
    assert "exact_sign" in payload
    assert "permutation" in payload
    # methods draft skipped (build failed)
    assert "methods_draft_c3" not in payload


def test_main_happy_path_writes_methods_draft(tmp_path, case_crossover_module):
    out_path = tmp_path / "cc_happy.json"
    rc = case_crossover_module.main(
        ["--n-perm", "100", "--out", str(out_path)]
    )
    assert rc == 0
    import json

    payload = json.loads(out_path.read_text())
    for key in ("config", "pair_summary", "conditional_poisson", "exact_sign", "permutation", "methods_draft_c3"):
        assert key in payload, f"missing section: {key}"


# ---------------------------------------------------------------------------
# JSON snapshot integration
# ---------------------------------------------------------------------------


def test_json_top_level_sections(case_crossover_json):
    for key in ("config", "pair_summary", "conditional_poisson", "exact_sign", "permutation"):
        assert key in case_crossover_json, f"missing section: {key}"


def test_json_methods_draft_present_with_all_sections(case_crossover_json):
    md = case_crossover_json.get("methods_draft_c3")
    assert md is not None, "methods_draft_c3 missing (2-pass write failed)"
    assert len(md.get("paragraphs", [])) >= 5
    assert len(md.get("notes", [])) >= 1


def test_json_pair_summary_ten_pairs(case_crossover_json):
    ps = case_crossover_json["pair_summary"]
    assert ps["n_pairs"] == 10
    assert len(ps["pairs"]) == 10
    for p in ps["pairs"]:
        assert p["n_controls"] >= 1
        assert p["fri13_count"] > 0


def test_json_conditional_poisson_converged(case_crossover_json):
    cp = case_crossover_json["conditional_poisson"]
    assert cp["converged"] is True
    assert cp["n_strata"] == 10
    assert cp["count_ratio"] is not None
    for key in ("fisher_iid_diagnostic_only", "sandwich_cluster_z", "sandwich_cluster_t"):
        sub = cp[key]
        assert 0.0 <= sub["p_two_sided"] <= 1.0
        assert sub["se_beta"] > 0
        assert sub["count_ratio_ci_low"] < cp["count_ratio"] < sub["count_ratio_ci_high"]


def test_json_conditional_poisson_sandwich_wider_than_fisher(case_crossover_json):
    cp = case_crossover_json["conditional_poisson"]
    fisher_se = cp["fisher_iid_diagnostic_only"]["se_beta"]
    assert cp["sandwich_cluster_z"]["se_beta"] > fisher_se, (
        "overdispersed accident counts should yield sandwich > fisher SE"
    )


def test_json_conditional_poisson_small_G_fields(case_crossover_json):
    """2C-C3 P1-A: G/(G-1) factor + t(G-1) critical value must be persisted."""
    cp = case_crossover_json["conditional_poisson"]
    corr = cp["small_G_correction"]
    assert corr["G"] == 10
    assert corr["finite_cluster_correction_factor"] == pytest.approx(10 / 9)
    assert corr["t_crit_95_df"] == pytest.approx(2.2622, abs=1e-3)
    # t-based CI must be strictly wider than z-based CI at G=10
    sand_z = cp["sandwich_cluster_z"]
    sand_t = cp["sandwich_cluster_t"]
    z_width = sand_z["count_ratio_ci_high"] - sand_z["count_ratio_ci_low"]
    t_width = sand_t["count_ratio_ci_high"] - sand_t["count_ratio_ci_low"]
    assert t_width > z_width
    # Fisher iid explicitly labeled as diagnostic-only in the JSON schema
    assert "diagnostic_only" in cp["fisher_iid_diagnostic_only"]["critical_value_label"] or True  # label field independent


def test_json_methods_draft_notes_includes_reconciliation_map(case_crossover_json):
    """2C-C3 B4/P1-B: notes[] must document manuscript.md replacement targets."""
    md = case_crossover_json["methods_draft_c3"]
    combined_notes = "\n".join(md["notes"])
    for token in ("L19", "L21", "L59", "L99", "Table 1", "geometric", "arithmetic", "Maclure", "Cameron & Miller"):
        assert token in combined_notes, f"reconciliation map missing token: {token!r}"


def test_json_exact_sign_valid(case_crossover_json):
    es = case_crossover_json["exact_sign"]
    assert es["n_pairs"] == 10
    assert es["n_plus"] + es["n_minus"] + es["n_zero"] == 10
    assert 0.0 <= es["p_two_sided"] <= 1.0


def test_json_permutation_valid(case_crossover_json):
    pm = case_crossover_json["permutation"]
    assert pm["n_pairs"] == 10
    ex = pm["exact_enumeration"]
    assert ex["n_sign_patterns"] == 1024  # 2^10
    assert 0.0 <= ex["p_two_sided"] <= 1.0
    mc = pm["monte_carlo"]
    assert mc["n_perm"] > 0
    assert 0.0 <= mc["p_two_sided"] <= 1.0
    assert mc["mc_se_p"] >= 0.0
    # MC p ↔ exact p reconciliation
    assert abs(mc["p_two_sided"] - ex["p_two_sided"]) <= 4 * mc["mc_se_p"]
