"""Tests for src/04_diagnostics.py — Phase 2C-C1 NB diagnostics.

Two kinds of checks:
  1. Module-level unit tests on helpers (_safe_exp, _safe_float, module load).
  2. JSON-level integration tests on the persisted diagnostics_results.json —
     these lock in the empirical range of the six diagnostic sections so a
     future accidental change to 02/03/04 is caught immediately.

The JSON-level tests skip when output/diagnostics_results.json is absent
(fresh checkout / CI without the full run).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------
def test_safe_exp_finite(diagnostics_module):
    assert diagnostics_module._safe_exp(0.0) == 1.0
    assert diagnostics_module._safe_exp(1.0) == math.e


def test_safe_exp_overflow_returns_none(diagnostics_module):
    assert diagnostics_module._safe_exp(1_000.0) is None
    assert diagnostics_module._safe_exp(float("inf")) is None
    assert diagnostics_module._safe_exp(float("nan")) is None


def test_safe_float_finite(diagnostics_module):
    assert diagnostics_module._safe_float(1.5) == 1.5
    assert diagnostics_module._safe_float(0) == 0.0


def test_safe_float_nonfinite_returns_none(diagnostics_module):
    assert diagnostics_module._safe_float(float("inf")) is None
    assert diagnostics_module._safe_float(float("nan")) is None


def test_specs_are_four_fits(diagnostics_module):
    specs = diagnostics_module.build_specs()
    labels = {s["label"] for s in specs}
    assert labels == {"02_primary", "02_sensitivity", "03_primary", "03_sensitivity"}


def test_spec_module_has_required_functions(diagnostics_module):
    specs = diagnostics_module.build_specs()
    for spec in specs:
        mod = spec["module"]
        for fn in ("load_prefecture_panel", "load_bureau_panel",
                   "build_design", "build_cluster_groups"):
            assert hasattr(mod, fn), f"{spec['label']} module missing {fn}"


# ---------------------------------------------------------------------------
# JSON-level integration tests
# ---------------------------------------------------------------------------
EXPECTED_SPECS = {"02_primary", "02_sensitivity", "03_primary", "03_sensitivity"}
EXPECTED_SECTIONS = {
    "dispersion",
    "pearson_residuals",
    "quasi_poisson",
    "hc1_robust_se",
    "spec_sensitivity",
    "pair_cluster_boot_pref_only",
    "methods_draft_c1",
}


def _find(entries, label):
    return next((e for e in entries if e.get("spec_label") == label), None)


def test_json_has_all_top_level_sections(diagnostics_json):
    d = diagnostics_json["diagnostics"]
    assert set(d.keys()) >= EXPECTED_SECTIONS


def test_json_dispersion_covers_all_four_specs(diagnostics_json):
    d = diagnostics_json["diagnostics"]["dispersion"]
    assert {e["spec_label"] for e in d} == EXPECTED_SPECS


def test_json_dispersion_03_primary_matches_2Ce(diagnostics_json):
    e = _find(diagnostics_json["diagnostics"]["dispersion"], "03_primary")
    assert e is not None
    # 2C-C2-e empirical values (see handoff-friday13th.md):
    #   count_ratio_nb2 = 1.0248, count_ratio_nb1 = 1.0275, |delta| = 0.003
    #   alpha_nb2 = 0.0234, alpha_nb1 = 0.4486
    assert 1.020 <= e["count_ratio_nb2"] <= 1.030
    if e["count_ratio_nb1"] is not None:
        assert e["count_ratio_abs_diff_nb2_vs_nb1"] is not None
        # Robustness assertion: parameterization-invariant claim requires
        # |nb2 - nb1| < 0.01. 2C-e observed 0.003.
        assert e["count_ratio_abs_diff_nb2_vs_nb1"] < 0.01
    assert 0.01 < e["alpha_nb2"] < 0.10


def test_json_pearson_03_primary_near_standard_normal(diagnostics_json):
    e = _find(diagnostics_json["diagnostics"]["pearson_residuals"], "03_primary")
    assert e is not None
    # Pearson residuals should be approximately N(0, 1) under correct
    # dispersion specification. 2C-e empirical: mean ~0, sd ~1.013.
    assert abs(e["mean"]) < 0.05
    assert 0.90 < e["sd"] < 1.15
    # Only 03_primary should have a figure_s1_path
    assert e["figure_s1_path"] is not None
    assert "S1_pearson_residuals_03_primary" in e["figure_s1_path"]


def test_json_pearson_other_specs_no_figure(diagnostics_json):
    """Only 03_primary emits Figure S1 (per PLAN 2C-C1 (b))."""
    for label in ("02_primary", "02_sensitivity", "03_sensitivity"):
        e = _find(diagnostics_json["diagnostics"]["pearson_residuals"], label)
        assert e is not None
        assert e["figure_s1_path"] is None


def test_json_quasi_poisson_matches_nb2_within_tolerance(diagnostics_json):
    """Quasi-Poisson count_ratio should match NB2 within ±0.02 — dispersion
    structure should not drive the null-everywhere claim."""
    disp = diagnostics_json["diagnostics"]["dispersion"]
    qp = diagnostics_json["diagnostics"]["quasi_poisson"]
    for label in EXPECTED_SPECS:
        d_e = _find(disp, label)
        q_e = _find(qp, label)
        assert d_e is not None and q_e is not None
        # NB2 and Quasi-Poisson use the same exp(coef) point estimate class;
        # a >0.02 divergence would indicate a spec mismatch.
        assert abs(d_e["count_ratio_nb2"] - q_e["count_ratio"]) < 0.02, (
            f"{label}: NB2 {d_e['count_ratio_nb2']:.4f} vs "
            f"QP {q_e['count_ratio']:.4f} diverges > 0.02"
        )
        assert q_e["scale_factor"] > 0


def test_json_hc1_ratio_within_plausible_range(diagnostics_json):
    """HC1/cluster_2way ratio typically 0.2-2.0 under day-level treatment
    (cluster SE is expected to be wider than HC1)."""
    for e in diagnostics_json["diagnostics"]["hc1_robust_se"]:
        assert e["is_fri13_se_hc1"] > 0
        assert e["is_fri13_se_cluster_2way"] > 0
        ratio = e["hc1_over_cluster_2way_ratio"]
        assert 0.2 <= ratio <= 5.0, f"{e['spec_label']}: HC1/cluster ratio={ratio}"


def test_json_spec_sensitivity_dummy_harmonic_converge(diagnostics_json):
    """dummy and harmonic MUST converge for all 4 specs; spline may be
    excluded (rank-deficient) — that's honestly reported, not a failure."""
    for e in diagnostics_json["diagnostics"]["spec_sensitivity"]:
        for kind in ("dummy", "harmonic"):
            r = e["seasonality_variants"][kind]
            assert r["converged"], f"{e['spec_label']}/{kind} did not converge"
            assert r["count_ratio"] is not None


def test_json_spec_sensitivity_null_robust(diagnostics_json):
    """max_abs_count_ratio_delta_vs_dummy < 0.05 across seasonality specs
    — the Fri13 null is insensitive to seasonality parameterization."""
    for e in diagnostics_json["diagnostics"]["spec_sensitivity"]:
        max_delta = e["max_abs_count_ratio_delta_vs_dummy"]
        # 03 primary observed 0.0004; 02 primary observed ~0.005.
        assert max_delta is not None
        assert max_delta < 0.05, f"{e['spec_label']}: spec-sensitivity delta={max_delta}"


def test_json_wildboot_all_specs_reported(diagnostics_json):
    """Every spec must have a bootstrap entry (skipped=True is acceptable)."""
    b = diagnostics_json["diagnostics"]["pair_cluster_boot_pref_only"]
    assert {e["spec_label"] for e in b} == EXPECTED_SPECS


def test_json_wildboot_pvalue_in_unit_interval(diagnostics_json):
    """When bootstrap ran, p_two_sided_boot must be in [0, 1]."""
    for e in diagnostics_json["diagnostics"]["pair_cluster_boot_pref_only"]:
        if e.get("skipped") or "error" in e:
            continue
        p = e["p_two_sided_boot"]
        assert 0.0 <= p <= 1.0, f"{e['spec_label']}: p_boot={p} outside [0,1]"


def test_json_wildboot_ci_ordered(diagnostics_json):
    """Bootstrap CI: low < high, both positive count_ratio."""
    for e in diagnostics_json["diagnostics"]["pair_cluster_boot_pref_only"]:
        if e.get("skipped") or "error" in e:
            continue
        assert e["count_ratio_ci_low_boot"] < e["count_ratio_ci_high_boot"]
        assert e["count_ratio_ci_low_boot"] > 0


def test_json_wildboot_convergence_rate_healthy(diagnostics_json):
    """When a full-scale (n_boot >= 100) run happened, at least 80% of iters
    should have converged. Skips for smoke runs where n_boot < 100."""
    for e in diagnostics_json["diagnostics"]["pair_cluster_boot_pref_only"]:
        if e.get("skipped") or "error" in e:
            continue
        if e["n_iter_requested"] < 100:
            continue
        rate = e["n_iter_successful"] / e["n_iter_requested"]
        assert rate >= 0.80, f"{e['spec_label']}: bootstrap success rate {rate:.2%}"


def test_json_methods_draft_populated(diagnostics_json):
    draft = diagnostics_json["diagnostics"]["methods_draft_c1"]
    assert "target_section" in draft
    assert "paragraphs" in draft
    # We expect at least 4 paragraphs (deviance/df, parameterization,
    # quasi-Poisson, robust SE, spec-sensitivity, bootstrap). The bootstrap
    # paragraph is added only when the bootstrap ran, so we assert 4 as a
    # lower bound and 6 as the target when everything ran.
    assert len(draft["paragraphs"]) >= 4
    assert draft["manuscript_reflection_phase"] == "2C-C5"


def test_json_config_captures_run_parameters(diagnostics_json):
    cfg = diagnostics_json["config"]
    assert "n_boot_requested" in cfg
    assert "bootstrap_seed" in cfg


def test_json_methods_draft_covers_all_six_diagnostics(diagnostics_json):
    """P1-5 M5 regression guard: Methods draft must reference each of the
    six diagnostics; a lone `len(paragraphs) >= 4` check let the missing
    Pearson paragraph slip through in the 2C-C1 review."""
    draft = diagnostics_json["diagnostics"]["methods_draft_c1"]
    text = " ".join(draft["paragraphs"]).lower()
    # Six required substrings (one per diagnostic)
    for needle in (
        "alpha",             # dispersion
        "pearson",           # (b) — the regression this test locks in
        "quasi-poisson",     # (c)
        "hc1",               # (d1)
        "seasonality",       # (d2) spec sensitivity
    ):
        assert needle in text, f"Methods draft missing '{needle}' coverage"
    # Bootstrap paragraph only exists if bootstrap actually ran (not
    # --skip-bootstrap); check presence conditionally.
    boot = diagnostics_json["diagnostics"]["pair_cluster_boot_pref_only"]
    if any(not e.get("skipped", False) and "error" not in e for e in boot):
        assert "bootstrap" in text, "Methods draft missing bootstrap coverage"


# ---------------------------------------------------------------------------
# Unit tests on the six core diagnostic functions (P2-9 M17 fix)
# ---------------------------------------------------------------------------
def test_unit_dispersion_diagnostic_shape(
    diagnostics_module, diagnostics_03_primary_ctx
):
    ctx = diagnostics_03_primary_ctx
    out = diagnostics_module.dispersion_diagnostic(ctx["fits"], ctx["spec"])
    for key in ("alpha_nb2", "count_ratio_nb2", "count_ratio_nb1",
                "count_ratio_abs_diff_nb2_vs_nb1", "n_obs", "k_params"):
        assert key in out, f"missing key: {key}"
    assert out["alpha_nb2"] is not None and 0.0 < out["alpha_nb2"] < 1.0
    assert 1.0 < out["count_ratio_nb2"] < 1.1
    if out["count_ratio_nb1"] is not None:
        assert out["count_ratio_abs_diff_nb2_vs_nb1"] < 0.01


def test_unit_pearson_diagnostic_returns_near_normal_stats(
    diagnostics_module, diagnostics_03_primary_ctx
):
    ctx = diagnostics_03_primary_ctx
    out = diagnostics_module.pearson_diagnostic(
        ctx["fits"], ctx["spec"], draw_figure=False
    )
    assert out["n"] > 100_000
    assert abs(out["mean"]) < 0.05
    assert 0.90 < out["sd"] < 1.15
    assert out["figure_s1_path"] is None  # draw_figure=False


def test_unit_quasi_poisson_matches_nb2_direct(
    diagnostics_module, diagnostics_03_primary_ctx
):
    ctx = diagnostics_03_primary_ctx
    out = diagnostics_module.quasi_poisson_diagnostic(
        ctx["y"], ctx["X"], ctx["groups"], ctx["spec"]
    )
    nb2_ratio = math.exp(float(ctx["fits"]["nb_iid"].params["is_fri13"]))
    assert abs(out["count_ratio"] - nb2_ratio) < 0.02
    assert out["scale_factor"] > 0
    assert out["is_fri13_se_cluster_2way"] > 0


def test_unit_hc1_diagnostic_returns_positive_se(
    diagnostics_module, diagnostics_03_primary_ctx
):
    ctx = diagnostics_03_primary_ctx
    out = diagnostics_module.hc1_diagnostic(ctx["fits"], ctx["spec"])
    assert out["is_fri13_se_hc1"] > 0
    assert out["is_fri13_se_cluster_2way"] > 0
    # In the current data, HC1 ≈ iid and cluster > HC1 (day-level treatment).
    assert 0.2 <= out["hc1_over_cluster_2way_ratio"] <= 5.0


def test_unit_build_design_alt_seasonality_shapes(
    diagnostics_module, diagnostics_03_primary_ctx
):
    ctx = diagnostics_03_primary_ctx
    for kind in ("dummy", "harmonic", "spline"):
        X_alt, y_alt = diagnostics_module._build_design_alt_seasonality(
            ctx["df"], ctx["spec"], kind
        )
        assert X_alt.shape[0] == ctx["df"].shape[0]
        assert "is_fri13" in X_alt.columns
        # month FE only in the dummy variant
        month_cols = [c for c in X_alt.columns if c.startswith("month_")]
        if kind == "dummy":
            assert len(month_cols) > 0
        else:
            assert len(month_cols) == 0


def test_unit_spec_sensitivity_dummy_matches_direct_nb2(
    diagnostics_module, diagnostics_03_primary_ctx
):
    ctx = diagnostics_03_primary_ctx
    out = diagnostics_module.spec_sensitivity_diagnostic(ctx["df"], ctx["spec"])
    dummy = out["seasonality_variants"]["dummy"]
    assert dummy["converged"]
    # dummy spec IS the 03_primary spec — count ratio must match the anchor.
    nb2_ratio = math.exp(float(ctx["fits"]["nb_iid"].params["is_fri13"]))
    assert abs(dummy["count_ratio"] - nb2_ratio) < 0.005
    # spline should be explicitly rank-deficient (honest exclusion)
    spline = out["seasonality_variants"]["spline"]
    assert spline["converged"] is False
    assert "partition-of-unity" in spline.get("error", "").lower() \
        or "intercept" in spline.get("error", "").lower()


def test_unit_pair_cluster_bootstrap_smoke_completes(
    diagnostics_module, diagnostics_03_primary_ctx
):
    """Smoke test with n_iter=8 — verifies the loop assembly + return schema.
    Real inference uses n_iter=500 via CLI."""
    ctx = diagnostics_03_primary_ctx
    out = diagnostics_module.pair_cluster_bootstrap(
        ctx["df"], ctx["spec"], n_iter=8, seed=12345
    )
    if "error" in out:
        # Should not happen at n_iter=8 for real data; if it does, the schema
        # still needs the standard failure keys.
        for key in ("n_iter_requested", "n_iter_successful",
                    "convergence_failures", "seed"):
            assert key in out
        return
    for key in ("n_iter_successful", "convergence_failures",
                "n_iter_with_runtime_warnings", "seed",
                "count_ratio_ci_low_boot", "count_ratio_ci_high_boot",
                "p_two_sided_boot", "mc_se_approx_p_two_sided"):
        assert key in out, f"missing key: {key}"
    assert 0.0 <= out["p_two_sided_boot"] <= 1.0
    assert out["count_ratio_ci_low_boot"] < out["count_ratio_ci_high_boot"]


def test_unit_pair_cluster_bootstrap_deterministic_under_seed(
    diagnostics_module, diagnostics_03_primary_ctx
):
    """B8 P3-13 fix regression: bootstrap must be reproducible under the
    same seed even if cluster ordering could otherwise drift (we now sort
    clusters before use)."""
    ctx = diagnostics_03_primary_ctx
    a = diagnostics_module.pair_cluster_bootstrap(
        ctx["df"], ctx["spec"], n_iter=5, seed=99
    )
    b = diagnostics_module.pair_cluster_bootstrap(
        ctx["df"], ctx["spec"], n_iter=5, seed=99
    )
    if "error" in a or "error" in b:
        return
    assert a["is_fri13_coef_mean"] == b["is_fri13_coef_mean"]
    assert a["is_fri13_coef_sd"] == b["is_fri13_coef_sd"]
