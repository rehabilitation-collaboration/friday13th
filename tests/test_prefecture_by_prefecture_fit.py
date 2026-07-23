"""Tests for src/07_prefecture_by_prefecture_fit.py (Phase 2C-C4).

Coverage:
  - safe helpers (finite/None handling)
  - zero-variance detection
  - design build with dropped covariates
  - fit_single_prefecture converged / non-converged flag structure
  - JSON snapshot integrity (top-level keys, values schema, diagnostics)
  - truth-values aggregation (max/min/median/CI exclusion count)
"""
from __future__ import annotations

import json

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------
def test_safe_float_finite_pass(pref_by_pref_module):
    assert pref_by_pref_module._safe_float(1.5) == 1.5
    assert pref_by_pref_module._safe_float(0) == 0.0


def test_safe_float_none_on_nan_or_inf(pref_by_pref_module):
    assert pref_by_pref_module._safe_float(float("nan")) is None
    assert pref_by_pref_module._safe_float(float("inf")) is None
    assert pref_by_pref_module._safe_float("not-a-number") is None


def test_safe_exp_overflow_returns_none(pref_by_pref_module):
    # exp(1000) overflows to inf; _safe_exp must map to None
    assert pref_by_pref_module._safe_exp(1000) is None
    assert pref_by_pref_module._safe_exp(0) == pytest.approx(1.0)
    assert pref_by_pref_module._safe_exp(float("nan")) is None


# ---------------------------------------------------------------------------
# Zero-variance + pairwise collinearity detection
# ---------------------------------------------------------------------------
def test_find_zero_variance_flags_constant_cols(pref_by_pref_module):
    df = pd.DataFrame({
        "precipitation_mm": [0.0, 1.0, 2.0],
        "snowfall_cm": [0.0, 0.0, 0.0],
        "snow_depth_max_cm": [5.0, 5.0, 5.0],  # constant non-zero -> std=0
    })
    dropped = pref_by_pref_module._find_zero_variance(
        df, ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")
    )
    assert set(dropped) == {"snowfall_cm", "snow_depth_max_cm"}


def test_find_zero_variance_handles_all_variance(pref_by_pref_module):
    df = pd.DataFrame({
        "precipitation_mm": [0.0, 1.0, 2.0],
        "snowfall_cm": [0.0, 1.0, 3.0],
        "snow_depth_max_cm": [1.0, 2.0, 5.0],
    })
    dropped = pref_by_pref_module._find_zero_variance(
        df, ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")
    )
    assert dropped == []


def test_find_pairwise_collinear_drops_perfect_pair(pref_by_pref_module):
    """Simulates the Ehime/Okayama pattern: snowfall and snow_depth exactly
    equal on the few non-zero days, corr = 1.0."""
    df = pd.DataFrame({
        "precipitation_mm": [0.0, 5.0, 10.0, 2.0, 0.0],
        "snowfall_cm": [0.0, 0.0, 0.0, 1.0, 0.0],
        "snow_depth_max_cm": [0.0, 0.0, 0.0, 1.0, 0.0],  # identical to snowfall
    })
    dropped = pref_by_pref_module._find_pairwise_collinear(
        df, ["snowfall_cm", "snow_depth_max_cm"]
    )
    # Keeps the earlier column, drops the later one.
    assert dropped == ["snow_depth_max_cm"]


def test_find_pairwise_collinear_keeps_uncorrelated(pref_by_pref_module):
    df = pd.DataFrame({
        "snowfall_cm": [0.0, 0.0, 0.0, 1.0, 0.0],
        "snow_depth_max_cm": [0.0, 2.0, 0.0, 0.0, 5.0],  # different pattern
    })
    dropped = pref_by_pref_module._find_pairwise_collinear(
        df, ["snowfall_cm", "snow_depth_max_cm"]
    )
    assert dropped == []


def test_find_dropped_covariates_combines_reasons(pref_by_pref_module):
    """Combined helper should report zero_variance and pairwise_collinear
    reasons in parallel with the dropped column list."""
    df = pd.DataFrame({
        "precipitation_mm": [0.0, 1.0, 2.0, 3.0, 4.0],
        "snowfall_cm": [0.0, 0.0, 0.0, 0.0, 0.0],   # zero variance
        "snow_depth_max_cm": [1.0, 1.0, 1.0, 1.0, 1.0],  # also zero variance (constant)
    })
    dropped, reasons = pref_by_pref_module._find_dropped_covariates(
        df, ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")
    )
    assert set(dropped) == {"snowfall_cm", "snow_depth_max_cm"}
    assert set(reasons) == {"zero_variance"}


def test_find_dropped_covariates_pairwise_reason(pref_by_pref_module):
    """When one of a pair has variance but they're perfectly correlated,
    the second column is dropped with reason=pairwise_collinear."""
    df = pd.DataFrame({
        "precipitation_mm": [0.0, 5.0, 10.0, 2.0, 0.0],
        "snowfall_cm": [0.0, 0.0, 0.0, 1.0, 0.0],
        "snow_depth_max_cm": [0.0, 0.0, 0.0, 1.0, 0.0],
    })
    dropped, reasons = pref_by_pref_module._find_dropped_covariates(
        df, ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")
    )
    assert dropped == ["snow_depth_max_cm"]
    assert reasons == ["pairwise_collinear"]


# ---------------------------------------------------------------------------
# Design build (verifies dropped covariates are excluded from exog)
# ---------------------------------------------------------------------------
def test_build_design_single_drops_covariates(pref_by_pref_module):
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=6, freq="D"),
        "total_count": [10, 12, 8, 11, 9, 13],
        "is_fri13": [0, 0, 0, 0, 0, 0],
        "is_13th": [0, 0, 0, 0, 0, 0],
        "is_holiday": [1, 0, 0, 0, 0, 0],
        "is_obon": [0, 0, 0, 0, 0, 0],
        "is_newyear": [1, 0, 0, 0, 0, 0],
        "cloud_cover": [50, 60, 70, 40, 30, 55],
        "precipitation_mm": [0, 1, 2, 3, 0, 1],
        "snowfall_cm": [0, 0, 0, 0, 0, 0],       # zero-var -> should be dropped
        "snow_depth_max_cm": [0, 0, 0, 0, 0, 0],  # zero-var -> should be dropped
        "year": [2020] * 6,
        "month": [1, 1, 1, 1, 1, 1],
        "weekday": [2, 3, 4, 5, 6, 0],
    })
    X, y = pref_by_pref_module.build_design_single(
        df, dropped_covariates=["snowfall_cm", "snow_depth_max_cm"]
    )
    assert "snowfall_cm" not in X.columns
    assert "snow_depth_max_cm" not in X.columns
    assert "is_fri13" in X.columns
    assert "precipitation_mm" in X.columns
    assert len(y) == 6


# ---------------------------------------------------------------------------
# fit_single_prefecture non-convergence structure
# ---------------------------------------------------------------------------
def test_fit_single_prefecture_non_conv_returns_flagged_dict(pref_by_pref_module):
    """Zero-row subset triggers a raise during Poisson fit — verifies the flag
    path returns a well-formed dict without crashing the whole run."""
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=3, freq="D"),
        "total_count": [10, 10, 10],  # constant y -> Poisson typically raises
        "is_fri13": [0, 0, 0],
        "is_13th": [0, 0, 0],
        "is_holiday": [0, 0, 0],
        "is_obon": [0, 0, 0],
        "is_newyear": [0, 0, 0],
        "cloud_cover": [50, 60, 70],
        "precipitation_mm": [0, 1, 2],
        "snowfall_cm": [0, 0, 0],
        "snow_depth_max_cm": [0, 0, 0],
        "year": [2020, 2020, 2020],
        "month": [1, 1, 1],
        "weekday": [2, 3, 4],
    })
    r = pref_by_pref_module.fit_single_prefecture(df, "TestPref")
    # Whether it converges is unimportant — what matters is the dict shape.
    assert r["prefecture_en"] == "TestPref"
    assert r["n_obs"] == 3
    assert isinstance(r["converged"], bool)
    assert "count_ratio" in r
    assert "is_fri13_p" in r
    assert "dropped_reason" in r
    # se_source is None until the HC1 refit succeeds (protects against B2 label drift).
    if not r["converged"]:
        assert r["se_source"] is None
    assert set(r["dropped_covariates"]) == {"snowfall_cm", "snow_depth_max_cm"}


# ---------------------------------------------------------------------------
# BH-FDR helper
# ---------------------------------------------------------------------------
def test_bh_fdr_significant_all_null(pref_by_pref_module):
    """No p <= (k/m)*q => zero significant."""
    pvals = [0.5, 0.6, 0.7, 0.8, 0.9]
    assert pref_by_pref_module._bh_fdr_significant(pvals, q=0.05) == 0


def test_bh_fdr_significant_all_true(pref_by_pref_module):
    """All p < smallest BH threshold => all significant."""
    pvals = [0.001, 0.002, 0.003]
    assert pref_by_pref_module._bh_fdr_significant(pvals, q=0.05) == 3


def test_bh_fdr_significant_mixed(pref_by_pref_module):
    """Standard step-up: with m=10 and q=0.05, threshold for the k=1 test is
    0.005; only p<=0.005 counts."""
    pvals = [0.001, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30, 0.90]
    result = pref_by_pref_module._bh_fdr_significant(pvals, q=0.05)
    # BH step-up: largest k where sorted p[k-1] <= k/10 * 0.05.
    #   k=1: 0.001 <= 0.005 ✓
    #   k=2: 0.02  <= 0.010 ✗ ; but step-up: check all k first, take max
    # Only k=1 passes -> 1 significant.
    assert result == 1


def test_bh_fdr_significant_empty(pref_by_pref_module):
    assert pref_by_pref_module._bh_fdr_significant([], q=0.05) == 0


# ---------------------------------------------------------------------------
# JSON snapshot integrity
# ---------------------------------------------------------------------------
def test_json_top_level_keys(pref_by_pref_json):
    for key in ("project", "phase", "generated", "script", "model_notes",
                "values", "diagnostics"):
        assert key in pref_by_pref_json, f"missing top-level key: {key}"
    assert pref_by_pref_json["project"] == "friday13th"
    assert pref_by_pref_json["phase"] == "2C-C4"


def test_json_diagnostics_47_prefectures(pref_by_pref_json):
    diag = pref_by_pref_json["diagnostics"]
    assert diag["n_prefectures"] == 47
    assert diag["n_converged"] + diag["n_non_converged"] == 47
    # After 2C-C4 pairwise-collinearity fix, all 47 must converge.
    assert diag["n_converged"] == 47
    assert len(diag["results"]) == 47
    # New field from write_results.
    assert "n_listwise_dropped" in diag
    assert isinstance(diag["n_listwise_dropped"], int)


def test_json_dropped_covariates_map_includes_zero_snow_prefs(pref_by_pref_json):
    """The 6 zero-variance prefectures + at least Ehime/Okayama (pairwise
    collinearity) must appear in the drop map, each with a reason string."""
    dropped_map = pref_by_pref_json["diagnostics"]["dropped_covariates_by_prefecture"]
    expected_zero_var = {"Kagawa", "Miyazaki", "Oita", "Okinawa", "Osaka", "Shizuoka"}
    assert set(dropped_map.keys()) >= expected_zero_var
    for pref in expected_zero_var:
        cols = {e["col"] for e in dropped_map[pref]}
        assert "snowfall_cm" in cols
        assert "snow_depth_max_cm" in cols
        for entry in dropped_map[pref]:
            assert entry["reason"] in ("zero_variance", "pairwise_collinear")
    # Ehime + Okayama were rescued by the pairwise-collinearity check.
    for pref in ("Ehime", "Okayama"):
        assert pref in dropped_map
        reasons = {e["reason"] for e in dropped_map[pref]}
        assert "pairwise_collinear" in reasons


def test_json_result_schema(pref_by_pref_json):
    results = pref_by_pref_json["diagnostics"]["results"]
    required_keys = {
        "prefecture_en", "n_obs", "dropped_covariates", "dropped_reason",
        "converged", "non_conv_reason", "alpha_mle_nb2", "is_fri13_coef",
        "is_fri13_se", "is_fri13_p", "count_ratio", "count_ratio_ci_low",
        "count_ratio_ci_high", "se_source", "nb2_runtime_warnings",
    }
    for r in results:
        assert required_keys.issubset(r.keys()), \
            f"missing keys in {r.get('prefecture_en')}: {required_keys - set(r.keys())}"
        # dropped_covariates and dropped_reason must be same length.
        assert len(r["dropped_covariates"]) == len(r["dropped_reason"])


def test_json_converged_results_have_finite_stats(pref_by_pref_json):
    """converged=True rows must have non-null coef/SE/ratio/CI/p and the
    corrected HC1 se_source label."""
    for r in pref_by_pref_json["diagnostics"]["results"]:
        if not r["converged"]:
            continue
        assert r["is_fri13_coef"] is not None
        assert r["is_fri13_se"] is not None and r["is_fri13_se"] > 0
        assert r["is_fri13_p"] is not None and 0 <= r["is_fri13_p"] <= 1
        assert r["count_ratio"] is not None and r["count_ratio"] > 0
        assert r["count_ratio_ci_low"] is not None
        assert r["count_ratio_ci_high"] is not None
        assert r["count_ratio_ci_low"] <= r["count_ratio"] <= r["count_ratio_ci_high"]
        # 2C-C4 P1 fix: se_source must reflect the actual HC1 estimator, not
        # the misleading "cluster_1way_date" label.
        assert r["se_source"] == "hc1_heteroscedasticity_robust"


def test_json_non_converged_results_have_null_stats(pref_by_pref_json):
    """converged=False rows must have all stats set to None (JSON null),
    including se_source (2C-C4 AKAGI B2 fix — no per-row label drift)."""
    for r in pref_by_pref_json["diagnostics"]["results"]:
        if r["converged"]:
            continue
        assert r["non_conv_reason"] is not None
        assert r["is_fri13_coef"] is None
        assert r["count_ratio"] is None
        assert r["count_ratio_ci_low"] is None
        assert r["count_ratio_ci_high"] is None
        assert r["se_source"] is None


def test_json_values_include_summary_stats(pref_by_pref_json):
    ids = {v["id"] for v in pref_by_pref_json["values"]}
    for expected_id in (
        "pref_by_pref_n_prefectures",
        "pref_by_pref_n_converged",
        "pref_by_pref_n_non_converged",
        "pref_by_pref_ratio_max_pref",
        "pref_by_pref_ratio_max",
        "pref_by_pref_ratio_min_pref",
        "pref_by_pref_ratio_min",
        "pref_by_pref_ratio_median",
        "pref_by_pref_n_ci_excludes_one",
        # 2C-C4 MAGI-AKAGI B4 fix: multi-test disclosure fields.
        "pref_by_pref_n_ci_excludes_one_binomial_p",
        "pref_by_pref_n_bonferroni_significant",
        "pref_by_pref_n_bh_fdr_significant",
    ):
        assert expected_id in ids, f"missing summary value id: {expected_id}"


def test_json_model_notes_reflects_hc1(pref_by_pref_json):
    """model_notes must describe HC1 (not the misleading 'cluster' label) so
    manuscript integration in C5 can't paste-in the wrong estimator name."""
    notes = pref_by_pref_json.get("model_notes", "")
    assert "HC1" in notes
    assert "pairwise-collinear" in notes or "pairwise_collinear" in notes


def test_json_no_ratio_exceeds_reasonable_bound(pref_by_pref_json):
    """Sanity: no prefecture should have a count ratio > 3 or < 0.3.
    A blown-out estimate would indicate a broken fit that slipped through."""
    for r in pref_by_pref_json["diagnostics"]["results"]:
        if r["converged"]:
            assert 0.3 < r["count_ratio"] < 3.0, \
                f"{r['prefecture_en']} ratio out of bounds: {r['count_ratio']}"


# ---------------------------------------------------------------------------
# truth-values aggregation
# ---------------------------------------------------------------------------
def test_build_truth_values_min_max_selection(pref_by_pref_module):
    fake_results = [
        {"prefecture_en": "A", "converged": True, "count_ratio": 1.5,
         "count_ratio_ci_low": 1.2, "count_ratio_ci_high": 1.8,
         "is_fri13_p": 0.0001},
        {"prefecture_en": "B", "converged": True, "count_ratio": 0.7,
         "count_ratio_ci_low": 0.5, "count_ratio_ci_high": 0.9,
         "is_fri13_p": 0.03},
        {"prefecture_en": "C", "converged": True, "count_ratio": 1.0,
         "count_ratio_ci_low": 0.9, "count_ratio_ci_high": 1.1,
         "is_fri13_p": 0.8},
        {"prefecture_en": "D", "converged": False, "count_ratio": None,
         "count_ratio_ci_low": None, "count_ratio_ci_high": None,
         "is_fri13_p": None},
    ]
    values = pref_by_pref_module.build_truth_values(fake_results)
    by_id = {v["id"]: v["value"] for v in values}
    assert by_id["pref_by_pref_n_prefectures"] == 4
    assert by_id["pref_by_pref_n_converged"] == 3
    assert by_id["pref_by_pref_n_non_converged"] == 1
    assert by_id["pref_by_pref_ratio_max_pref"] == "A"
    assert by_id["pref_by_pref_ratio_max"] == 1.5
    assert by_id["pref_by_pref_ratio_min_pref"] == "B"
    assert by_id["pref_by_pref_ratio_min"] == 0.7
    assert by_id["pref_by_pref_ratio_median"] == 1.0
    # A CI [1.2, 1.8] excludes 1.0; B CI [0.5, 0.9] excludes 1.0. Total = 2.
    assert by_id["pref_by_pref_n_ci_excludes_one"] == 2
    # Multi-test disclosure: 3 tests total, alpha_family=0.05 -> Bonferroni
    # threshold = 0.0167; only A (p=0.0001) passes -> 1 significant.
    assert by_id["pref_by_pref_n_bonferroni_significant"] == 1
    # binom(2, 3, 0.05, greater) is small but positive.
    assert 0 < by_id["pref_by_pref_n_ci_excludes_one_binomial_p"] <= 1
    # BH-FDR q=0.05 with p=[0.0001, 0.03, 0.8]:
    # k=1: 0.0001<=0.0167 ✓ ; k=2: 0.03<=0.0333 ✓ ; k=3: 0.8<=0.05 ✗
    # max k=2 -> 2 significant.
    assert by_id["pref_by_pref_n_bh_fdr_significant"] == 2


def test_build_truth_values_empty_converged_omits_extrema(pref_by_pref_module):
    """If no prefecture converges, ratio_max / ratio_min entries must be
    absent (not None) so the truth.json contract stays clean."""
    fake_results = [
        {"prefecture_en": "A", "converged": False, "count_ratio": None,
         "count_ratio_ci_low": None, "count_ratio_ci_high": None,
         "is_fri13_p": None},
    ]
    values = pref_by_pref_module.build_truth_values(fake_results)
    ids = {v["id"] for v in values}
    assert "pref_by_pref_n_prefectures" in ids
    assert "pref_by_pref_ratio_max" not in ids
    assert "pref_by_pref_ratio_min" not in ids


# ---------------------------------------------------------------------------
# write_results direct unit test (2C-C4 MAGI-AKAGI D-01 fix)
# ---------------------------------------------------------------------------
def test_write_results_direct_writes_valid_json(pref_by_pref_module, tmp_path):
    """Directly exercise write_results with a fake results list — verifies
    allow_nan=False, utf-8 encoding, model_notes text, dropped map schema."""
    fake = [
        {
            "prefecture_en": "Foo",
            "n_obs": 100,
            "dropped_covariates": ["snow_depth_max_cm"],
            "dropped_reason": ["pairwise_collinear"],
            "converged": True,
            "non_conv_reason": None,
            "alpha_mle_nb2": 0.05,
            "is_fri13_coef": 0.01,
            "is_fri13_se": 0.05,
            "is_fri13_p": 0.84,
            "count_ratio": 1.01,
            "count_ratio_ci_low": 0.92,
            "count_ratio_ci_high": 1.11,
            "se_source": "hc1_heteroscedasticity_robust",
            "nb2_runtime_warnings": [],
        },
    ]
    out = tmp_path / "test_out.json"
    pref_by_pref_module.write_results(fake, out, n_listwise_dropped=7)
    assert out.exists()
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["phase"] == "2C-C4"
    assert "HC1" in parsed["model_notes"]
    assert parsed["diagnostics"]["n_listwise_dropped"] == 7
    # dropped_covariates_by_prefecture uses the {col, reason} schema.
    dropped_map = parsed["diagnostics"]["dropped_covariates_by_prefecture"]
    assert "Foo" in dropped_map
    assert dropped_map["Foo"] == [{"col": "snow_depth_max_cm", "reason": "pairwise_collinear"}]


def test_write_results_rejects_nan(pref_by_pref_module, tmp_path):
    """allow_nan=False must refuse NaN inside the results list."""
    import math as _m
    fake = [
        {
            "prefecture_en": "Bar",
            "n_obs": 100,
            "dropped_covariates": [],
            "dropped_reason": [],
            "converged": True,
            "non_conv_reason": None,
            "alpha_mle_nb2": _m.nan,  # NaN slipped in — must be rejected
            "is_fri13_coef": 0.01,
            "is_fri13_se": 0.05,
            "is_fri13_p": 0.5,
            "count_ratio": 1.01,
            "count_ratio_ci_low": 0.92,
            "count_ratio_ci_high": 1.11,
            "se_source": "hc1_heteroscedasticity_robust",
            "nb2_runtime_warnings": [],
        },
    ]
    out = tmp_path / "test_out.json"
    with pytest.raises(ValueError, match="[Nn]a[Nn]"):
        pref_by_pref_module.write_results(fake, out, n_listwise_dropped=0)


def test_load_prefecture_panel_returns_tuple(pref_by_pref_module):
    """load_prefecture_panel now returns (df, n_listwise_dropped)."""
    if not pref_by_pref_module.PREF_ACC.exists():
        pytest.skip("PREF_ACC parquet missing")
    result = pref_by_pref_module.load_prefecture_panel()
    assert isinstance(result, tuple) and len(result) == 2
    df, n_dropped = result
    assert isinstance(n_dropped, int) and n_dropped >= 0
    assert "prefecture_en" in df.columns
