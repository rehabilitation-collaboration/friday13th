"""Contract tests for Phase 2C-C2-e weather+holiday adjusted NB panel.

Guards:
  - Panel loaders merge weather (precip/snow/snow_depth) and drop rows with
    any-null weather covariates (listwise). Post-listwise row count matches
    the expected raw-panel-size minus the observed 16-row deletion.
  - is_holiday / is_obon / is_newyear are present in the input panel AND in
    the design matrix (they enter as MAIN_EFFECTS, not as dummy-expanded FE).
  - Weather covariates enter the design; all three (precip/snow/snow_depth)
    are in MAIN_EFFECTS after the multicollinearity pre-check
    (|max r|=0.15, VIF=1.42 — both well within main-model tolerances).
  - Primary and sensitivity NB MLE converge on the enlarged design.
  - is_fri13 count_ratio stays inside a scientifically plausible range.
  - Primary (47 pref FE) and Sensitivity (51 bureau FE) agree numerically
    (case Z design validation, same as 2C-c).
  - Confounder directions match expectations: national holidays / Obon /
    New Year all reduce accident counts (coef < 0). If a sign flips, the
    holiday flag is likely miscoded upstream.
  - diff_vs_prior successfully joins to the 2C-c JSON so the manuscript
    parallel-report path is exercised.
  - write_results emits phase='2C-C2-e' and RFC-8259 compliant JSON.

Session-scoped fixtures pay the NB MLE cost once (roughly 30s wall).
"""
from __future__ import annotations

import math

import pytest

# Observed listwise deletion under the current weather panel: 16 rows total /
# 5 stations across BOTH the prefecture-level and bureau-level panels:
#   - precipitation_mm null: 15 rows across 4 stations
#       47615 x 10 (Jul-Aug 2022, following a heavy-rain sequence — MNAR-consistent
#                   rain-gauge saturation; see 03 docstring / Limitations)
#       47607 x 2  (2021-12-24, 2022-01-05)
#       47813 x 2  (2021-08-20, 2021-08-21)
#       47605 x 1  (2022-12-19, snowfall_cm=13 that day — precip-fillna(0) rejected)
#   - snow_depth_max_cm null: 1 row at station 47807 on 2022-11-10
# Locked as a contract because if the count changes silently, either the master
# cache was rebuilt or a NaN was accidentally introduced downstream.
EXPECTED_LISTWISE_DROP = 16
PREFECTURE_RAW_ROWS = 47 * 2192   # = 103,024
BUREAU_RAW_ROWS = 51 * 2192       # = 111,792

# Empirical guards, tuned after 2C-C2-e run (alpha ~ 0.023 for both models).
# alpha < 0.1 is tighter than the < 0.5 guard used in 2C-c because the enlarged
# model absorbs more variance; if alpha shoots back up to ~0.5 something has
# regressed in the design.
ALPHA_UPPER_TIGHT = 0.1

# Plausibility band for is_fri13 count_ratio (same as 2C-c: any effect outside
# 0.8-1.3 is a design bug, not a real Fri13 effect).
COUNT_RATIO_PLAUSIBLE_LOW = 0.8
COUNT_RATIO_PLAUSIBLE_HIGH = 1.3

# Primary vs sensitivity should still agree to within 1% after weather/holiday.
PRIMARY_SENSITIVITY_RATIO_TOL = 0.01


@pytest.fixture(scope="session")
def prefecture_weather_panel(weather_nb_module):
    for p in (
        weather_nb_module.PREF_ACC,
        weather_nb_module.PREF_CLD,
        weather_nb_module.PREF_WTH,
    ):
        if not p.exists():
            pytest.skip(f"required parquet missing: {p}")
    return weather_nb_module.load_prefecture_panel()


@pytest.fixture(scope="session")
def bureau_weather_panel(weather_nb_module):
    for p in (
        weather_nb_module.BUR_ACC,
        weather_nb_module.BUR_CLD,
        weather_nb_module.BUR_WTH,
    ):
        if not p.exists():
            pytest.skip(f"required parquet missing: {p}")
    return weather_nb_module.load_bureau_panel()


@pytest.fixture(scope="session")
def primary_weather_fit(weather_nb_module, prefecture_weather_panel):
    X, y = weather_nb_module.build_design(
        prefecture_weather_panel, weather_nb_module.DUMMY_COLS
    )
    groups = weather_nb_module.build_cluster_groups(prefecture_weather_panel)
    return weather_nb_module.fit_nb_panel(y, X, groups, label="pref_weather")


@pytest.fixture(scope="session")
def sensitivity_weather_fit(weather_nb_module, bureau_weather_panel):
    X, y = weather_nb_module.build_design(
        bureau_weather_panel, weather_nb_module.BUREAU_DUMMY_COLS
    )
    groups = weather_nb_module.build_cluster_groups(bureau_weather_panel)
    return weather_nb_module.fit_nb_panel(y, X, groups, label="bureau_weather")


# ---------------------------------------------------------------------------
# Panel loaders + listwise deletion
# ---------------------------------------------------------------------------
def test_prefecture_panel_listwise_deletion_count(prefecture_weather_panel):
    """Post-listwise row count must equal raw panel size minus 16."""
    expected = PREFECTURE_RAW_ROWS - EXPECTED_LISTWISE_DROP
    assert prefecture_weather_panel.shape[0] == expected, (
        prefecture_weather_panel.shape[0],
        expected,
    )


def test_bureau_panel_listwise_deletion_count(bureau_weather_panel):
    expected = BUREAU_RAW_ROWS - EXPECTED_LISTWISE_DROP
    assert bureau_weather_panel.shape[0] == expected, (
        bureau_weather_panel.shape[0],
        expected,
    )


def test_weather_columns_have_no_nulls_after_listwise(prefecture_weather_panel):
    for c in ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm"):
        assert prefecture_weather_panel[c].isna().sum() == 0, c


def test_holiday_flags_present_and_binary(prefecture_weather_panel):
    for c in ("is_holiday", "is_obon", "is_newyear"):
        assert c in prefecture_weather_panel.columns, c
        assert set(prefecture_weather_panel[c].unique()) <= {0, 1}, c


def test_obon_flag_matches_hardcoded_dates(prefecture_weather_panel):
    """is_obon should be exactly 8/13-16 for each of 6 years x 47 pref."""
    obon = prefecture_weather_panel[prefecture_weather_panel["is_obon"] == 1]
    assert obon["month"].eq(8).all()
    assert obon["day_of_month"].between(13, 16).all()
    # 6 years x 4 days x 47 pref (no listwise deletion affects Obon dates in
    # 2019-2024 based on MS-2 investigation)
    assert obon.shape[0] == 6 * 4 * 47


# ---------------------------------------------------------------------------
# Design matrix
# ---------------------------------------------------------------------------
def test_build_design_includes_weather_and_holiday(
    weather_nb_module, prefecture_weather_panel
):
    X, _ = weather_nb_module.build_design(
        prefecture_weather_panel, weather_nb_module.DUMMY_COLS
    )
    required = {
        "is_fri13", "is_13th",
        "is_holiday", "is_obon", "is_newyear",
        "cloud_cover", "precipitation_mm", "snowfall_cm", "snow_depth_max_cm",
        "const",
    }
    assert required <= set(X.columns), required - set(X.columns)
    assert X.notna().all().all()


def test_main_effects_constant_contains_all_nine_covariates(weather_nb_module):
    """Design carries 2 fri13-related + 3 holiday + 4 weather = 9 MAIN_EFFECTS."""
    assert len(weather_nb_module.MAIN_EFFECTS) == 9
    assert "is_fri13" in weather_nb_module.MAIN_EFFECTS
    assert set(weather_nb_module.HOLIDAY_COLS) <= set(weather_nb_module.MAIN_EFFECTS)
    assert set(weather_nb_module.WEATHER_COLS) <= set(weather_nb_module.MAIN_EFFECTS)


# ---------------------------------------------------------------------------
# Fits — primary and sensitivity
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_primary_weather_converged(primary_weather_fit):
    assert primary_weather_fit["converged"] is True
    assert primary_weather_fit["family"] == "NegativeBinomial(nb2)"
    assert primary_weather_fit["n_clusters_pref"] == 47
    assert primary_weather_fit["n_clusters_date"] == 2192


@pytest.mark.slow
def test_primary_weather_alpha_tighter_than_2c_c(primary_weather_fit):
    """After weather+holiday adjustment, alpha should be < 0.1 (empirically
    ~0.023). If it drifts back near the 2C-c 0.5 guard, the enlarged model
    isn't absorbing what it should."""
    alpha = primary_weather_fit["alpha_mle_nb2"]
    assert alpha > 0
    assert alpha < ALPHA_UPPER_TIGHT, (
        f"MLE alpha={alpha:.4f} exceeds tight guard {ALPHA_UPPER_TIGHT}; "
        "the weather+holiday model should absorb more overdispersion than 2C-c."
    )


@pytest.mark.slow
def test_primary_weather_count_ratio_plausible(primary_weather_fit):
    cl = primary_weather_fit["cluster_se"]
    assert cl["se_source"] == "cluster_2way_pref_date"
    assert cl["is_fri13_se"] > 0
    assert math.isfinite(cl["count_ratio"])
    assert cl["count_ratio_ci_low"] < cl["count_ratio"] < cl["count_ratio_ci_high"]
    assert COUNT_RATIO_PLAUSIBLE_LOW <= cl["count_ratio"] <= COUNT_RATIO_PLAUSIBLE_HIGH


@pytest.mark.slow
def test_confounder_signs_match_expectations(primary_weather_fit):
    """National holidays / Obon / New Year all cut traffic → coef < 0 with
    material magnitude and clear statistical significance. A near-zero-but-
    negative coefficient (coef=-1e-6, p=0.98) would pass a bare sign check
    but wouldn't support the docstring claim that these flags 'reduce accident
    counts' — so we also assert count_ratio < 0.95 (>=5% reduction) and
    p < 0.001 (P3-8 tightening, empirical: all three are ~1e-19 to 1e-57)."""
    confounders = primary_weather_fit["weather_coefs"]
    for name in ("is_holiday", "is_obon", "is_newyear"):
        assert name in confounders, name
        block = confounders[name]
        assert block["coef"] < 0, (
            f"{name} coef={block['coef']} — expected negative "
            "(holidays / Obon / New Year reduce traffic volume)"
        )
        assert block["count_ratio"] < 0.95, (
            f"{name} count_ratio={block['count_ratio']:.4f} — expected "
            "material reduction (< 0.95); a near-zero-negative coefficient "
            "would pass a bare sign check but wouldn't match the design intent."
        )
        assert block["p"] < 1e-3, (
            f"{name} p={block['p']} — confounder must be clearly significant "
            "for its adjustment role to be defensible in review."
        )


@pytest.mark.slow
def test_all_main_effects_present_in_weather_coefs(primary_weather_fit, weather_nb_module):
    """P3-10: `_extract_weather_holiday_coefs` silently skips missing
    covariates via `if name not in fit.params.index: continue`. Currently
    unreachable, but a typo added to MAIN_EFFECTS would vanish silently
    from diagnostics with no test failing. Lock all 8 non-Fri13 MAIN_EFFECTS
    as required keys."""
    confounders = primary_weather_fit["weather_coefs"]
    expected = set(weather_nb_module.MAIN_EFFECTS) - {"is_fri13"}
    assert expected <= set(confounders.keys()), expected - set(confounders.keys())


@pytest.mark.slow
def test_is_fri13_count_ratio_robust_across_nb1_nb2(
    primary_weather_fit, sensitivity_weather_fit
):
    """P2-4 fix: alpha diverges 19x between nb1 and nb2 (spec-dependent
    dispersion parameter), but the is_fri13 count_ratio (the actual primary
    result) must be stable across parameterizations for the null-everywhere
    claim to survive reviewer scrutiny. Empirically ~0.3% divergence in 2C-e."""
    for fit in (primary_weather_fit, sensitivity_weather_fit):
        nb1_ratio = fit["is_fri13_ratio_nb1"]
        nb2_ratio = fit["cluster_se"]["count_ratio"]
        assert nb1_ratio is not None, "nb1 refit failed — parameterization robustness untested"
        assert abs(nb1_ratio - nb2_ratio) < 0.01, (
            f"{fit['label']}: nb1 ratio={nb1_ratio:.4f} vs nb2 ratio={nb2_ratio:.4f} "
            f"diff={abs(nb1_ratio - nb2_ratio):.4f} — is_fri13 estimate is "
            "spec-dependent, undermines robustness claim."
        )


@pytest.mark.slow
def test_nb2_runtime_warnings_captured_field_exists(primary_weather_fit):
    """P2-2 fix: nb2 fit_iid RuntimeWarnings are captured (not silently
    emitted to stderr) and surfaced as a list in the fit result. Empty list
    means the fit was numerically clean; non-empty list means the caller
    can decide whether to escalate. Test asserts the field EXISTS as a list
    (its non-emptiness reflects a real statsmodels/BFGS behaviour we do not
    control from this side, so we do not assert emptiness here)."""
    warnings_list = primary_weather_fit["nb2_runtime_warnings"]
    assert isinstance(warnings_list, list)
    for w in warnings_list:
        assert isinstance(w, str)


@pytest.mark.slow
def test_sensitivity_weather_converged_and_plausible(sensitivity_weather_fit):
    assert sensitivity_weather_fit["converged"] is True
    cl = sensitivity_weather_fit["cluster_se"]
    assert cl["is_fri13_se"] > 0
    assert math.isfinite(cl["count_ratio"])
    assert COUNT_RATIO_PLAUSIBLE_LOW <= cl["count_ratio"] <= COUNT_RATIO_PLAUSIBLE_HIGH
    # Cluster axis is still prefecture (47), NOT pref_code (51), same as 02.
    assert sensitivity_weather_fit["n_clusters_pref"] == 47


@pytest.mark.slow
def test_primary_and_sensitivity_agree(primary_weather_fit, sensitivity_weather_fit):
    p = primary_weather_fit["cluster_se"]["count_ratio"]
    s = sensitivity_weather_fit["cluster_se"]["count_ratio"]
    diff = abs(p - s)
    assert diff < PRIMARY_SENSITIVITY_RATIO_TOL, (
        f"primary count_ratio={p:.4f} vs sensitivity count_ratio={s:.4f} "
        f"diff={diff:.4f} exceeds tolerance {PRIMARY_SENSITIVITY_RATIO_TOL}"
    )


# ---------------------------------------------------------------------------
# Diff vs prior + JSON output
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_diff_vs_prior_wired_to_2c_c(
    weather_nb_module, primary_weather_fit, sensitivity_weather_fit
):
    """2C-c prefecture_panel_results.json must exist and diff_vs_prior must
    populate both primary and sensitivity delta blocks — this is the
    parallel-reporting path the manuscript relies on.

    P3-4 fix: also asserts prior_ci and new_ci contain finite numbers, not
    silent Nones — the prior code path had bare `.get()` with no default for
    the CI bounds, so a prior JSON schema drift renaming those ids would
    have silently written `[null, null]` into the output with no test failure.
    """
    diff = weather_nb_module.diff_vs_prior(primary_weather_fit, sensitivity_weather_fit)
    assert diff is not None, "prior 2C-c results missing — parallel report broken"
    assert diff["prior_phase"] == "2C-C2-c"
    for name in ("primary_47_prefecture", "sensitivity_51_bureau"):
        block = diff[name]
        for k in ("prior_count_ratio", "new_count_ratio", "prior_p", "new_p"):
            assert block[k] is not None, (name, k)
        assert math.isfinite(block["delta_count_ratio"])
        for side in ("prior_ci", "new_ci"):
            ci = block[side]
            assert ci[0] is not None and ci[1] is not None, (name, side, ci)
            assert math.isfinite(ci[0]) and math.isfinite(ci[1]), (name, side, ci)


@pytest.mark.slow
def test_write_weather_results_phase_and_rfc8259(
    weather_nb_module, primary_weather_fit, sensitivity_weather_fit, tmp_path
):
    import json

    out = tmp_path / "weather_holiday_nb_results.json"
    weather_nb_module.write_results(primary_weather_fit, sensitivity_weather_fit, out)
    raw = out.read_text(encoding="utf-8")
    assert "NaN" not in raw and "Infinity" not in raw

    doc = json.loads(raw)
    assert doc["project"] == "friday13th"
    assert doc["phase"] == "2C-C2-e"
    assert doc["script"] == "src/03_prefecture_panel_weather_nb.py"
    assert "diff_vs_2c_c_unadjusted" in doc
    assert isinstance(doc["values"], list) and doc["values"]
