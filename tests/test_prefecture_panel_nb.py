"""Contract tests for the prefecture/bureau NB panel regression.

Guards:
  - Panel loaders return a merged frame with expected shape and no NaN cloud_cover.
  - build_design produces a full-rank design matrix with is_fri13 + is_13th present.
  - Primary NB MLE converges, alpha > 0, two-way cluster SE > 0, count_ratio finite
    AND inside a scientifically plausible range (0.8-1.3).
  - Sensitivity NB MLE converges (fallback path removed with YAGNI).
  - Primary (47 pref FE) and Sensitivity (51 bureau FE) agree numerically —
    this is the validation criterion for design 案Z (both-report design).
  - Truth values emitted for manuscript verification carry every required
    field of the _v() schema (id/value/label/section/format) and required IDs.
  - Output JSON is RFC-8259 compliant (no bare NaN).

`primary_fit`/`sensitivity_fit` fixtures are session-scoped so the NB MLE cost is paid once.
"""
from __future__ import annotations

import math

import pytest

REQUIRED_TRUTH_FIELDS = {"id", "value", "label", "section", "format"}
REQUIRED_CLUSTER_FIELDS = {
    "se_source",
    "is_fri13_coef",
    "is_fri13_se",
    "is_fri13_z",
    "is_fri13_p",
    "count_ratio",
    "count_ratio_ci_low",
    "count_ratio_ci_high",
}

# Plausible range for a Fri13 effect on Japanese traffic accidents. If a code
# regression pushes count_ratio outside this window, something is wrong at the
# design/coefficient level, not a real effect.
COUNT_RATIO_PLAUSIBLE_LOW = 0.8
COUNT_RATIO_PLAUSIBLE_HIGH = 1.3

# Primary (47 pref FE) and sensitivity (51 bureau FE) should agree on the
# is_fri13 count_ratio to within ~1% — the two models estimate the same
# quantity from the same underlying accident-day cells, only rolling up
# Hokkaido differently.
PRIMARY_SENSITIVITY_RATIO_TOL = 0.01
PRIMARY_SENSITIVITY_ALPHA_TOL = 0.005


@pytest.fixture(scope="session")
def prefecture_panel(nb_module):
    if not nb_module.PREF_ACC.exists() or not nb_module.PREF_CLD.exists():
        pytest.skip("prefecture panel parquet missing (run 01a/01b first)")
    return nb_module.load_prefecture_panel()


@pytest.fixture(scope="session")
def bureau_panel(nb_module):
    if not nb_module.BUR_ACC.exists() or not nb_module.BUR_CLD.exists():
        pytest.skip("bureau panel parquet missing (run 01a/01b first)")
    return nb_module.load_bureau_panel()


@pytest.fixture(scope="session")
def primary_fit(nb_module, prefecture_panel):
    X, y = nb_module.build_design(prefecture_panel, nb_module.DUMMY_COLS)
    groups = nb_module.build_cluster_groups(prefecture_panel)
    return nb_module.fit_nb_panel(y, X, groups, label="prefecture_47_FE")


@pytest.fixture(scope="session")
def sensitivity_fit(nb_module, bureau_panel):
    X, y = nb_module.build_design(bureau_panel, nb_module.BUREAU_DUMMY_COLS)
    groups = nb_module.build_cluster_groups(bureau_panel)
    return nb_module.fit_nb_panel(y, X, groups, label="bureau_51_FE")


# ---------------------------------------------------------------------------
# Panel / design
# ---------------------------------------------------------------------------
def test_prefecture_panel_shape(prefecture_panel):
    assert prefecture_panel.shape[0] == 47 * 2192
    assert prefecture_panel["cloud_cover"].isna().sum() == 0
    assert prefecture_panel["prefecture_en"].nunique() == 47
    assert set(prefecture_panel["is_fri13"].unique()) <= {0, 1}
    assert set(prefecture_panel["is_13th"].unique()) <= {0, 1}


def test_bureau_panel_shape(bureau_panel):
    assert bureau_panel.shape[0] == 51 * 2192
    assert bureau_panel["cloud_cover"].isna().sum() == 0
    assert bureau_panel["pref_code"].nunique() == 51
    # bureau panel also carries prefecture_en for the cluster axis
    assert bureau_panel["prefecture_en"].nunique() == 47


def test_build_design_prefecture(nb_module, prefecture_panel):
    X, y = nb_module.build_design(prefecture_panel, nb_module.DUMMY_COLS)
    for col in ("is_fri13", "is_13th", "cloud_cover", "const"):
        assert col in X.columns, col
    assert len(X) == len(prefecture_panel)
    assert len(y) == len(prefecture_panel)
    # 46 pref + 5 year + 11 month + 6 weekday + is_fri13 + is_13th + cloud + const
    assert X.shape[1] == 46 + 5 + 11 + 6 + 4
    assert X.notna().all().all()


def test_build_design_bureau(nb_module, bureau_panel):
    X, _ = nb_module.build_design(bureau_panel, nb_module.BUREAU_DUMMY_COLS)
    # 50 pref_code + 5 year + 11 month + 6 weekday + is_fri13 + is_13th + cloud + const
    assert X.shape[1] == 50 + 5 + 11 + 6 + 4


def test_build_cluster_groups_shape(nb_module, prefecture_panel):
    g = nb_module.build_cluster_groups(prefecture_panel)
    assert g.shape == (len(prefecture_panel), 2)
    # 47 prefectures x 2192 days
    assert len(set(g[:, 0])) == 47
    assert len(set(g[:, 1])) == 2192


# ---------------------------------------------------------------------------
# Primary fit
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_primary_converged(primary_fit):
    assert primary_fit["converged"] is True
    assert primary_fit["family"] == "NegativeBinomial(nb2)"


@pytest.mark.slow
def test_primary_alpha_positive_and_far_from_one(primary_fit):
    """MLE alpha must be > 0 and clearly distinct from the fixed alpha=1.0
    used by 02_main_analysis::adjusted_negbin(). If alpha comes back near 1.0
    the switch to MLE was pointless."""
    alpha = primary_fit["alpha_mle_nb2"]
    assert alpha > 0
    assert alpha < 0.5, f"MLE alpha={alpha} is too close to the old fixed 1.0"


@pytest.mark.slow
def test_primary_cluster_stats_within_plausible_range(primary_fit):
    cl = primary_fit["cluster_se"]
    assert REQUIRED_CLUSTER_FIELDS <= set(cl)
    assert cl["se_source"] == "cluster_2way_pref_date"
    assert cl["is_fri13_se"] > 0
    assert math.isfinite(cl["count_ratio"])
    assert cl["count_ratio"] > 0
    assert cl["count_ratio_ci_low"] < cl["count_ratio"] < cl["count_ratio_ci_high"]
    # Plausibility band: catches gross coefficient-scale bugs (e.g. ratio 5.0)
    assert COUNT_RATIO_PLAUSIBLE_LOW <= cl["count_ratio"] <= COUNT_RATIO_PLAUSIBLE_HIGH, (
        f"primary count_ratio={cl['count_ratio']} outside plausible "
        f"[{COUNT_RATIO_PLAUSIBLE_LOW}, {COUNT_RATIO_PLAUSIBLE_HIGH}]"
    )
    assert primary_fit["n_clusters_pref"] == 47
    assert primary_fit["n_clusters_date"] == 2192


# ---------------------------------------------------------------------------
# Sensitivity fit
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_sensitivity_converged_and_plausible(sensitivity_fit):
    assert sensitivity_fit["converged"] is True
    assert sensitivity_fit["family"] == "NegativeBinomial(nb2)"
    cl = sensitivity_fit["cluster_se"]
    assert REQUIRED_CLUSTER_FIELDS <= set(cl)
    assert cl["is_fri13_se"] > 0
    assert math.isfinite(cl["count_ratio"])
    assert COUNT_RATIO_PLAUSIBLE_LOW <= cl["count_ratio"] <= COUNT_RATIO_PLAUSIBLE_HIGH
    # Cluster axis is prefecture (47), NOT pref_code (51) — that's the whole
    # point of the F8 fix.
    assert sensitivity_fit["n_clusters_pref"] == 47
    assert sensitivity_fit["n_clusters_date"] == 2192


# ---------------------------------------------------------------------------
# Cross-model agreement (design 案Z validation criterion)
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_primary_and_sensitivity_agree_on_count_ratio(primary_fit, sensitivity_fit):
    p = primary_fit["cluster_se"]["count_ratio"]
    s = sensitivity_fit["cluster_se"]["count_ratio"]
    diff = abs(p - s)
    assert diff < PRIMARY_SENSITIVITY_RATIO_TOL, (
        f"primary count_ratio={p:.4f} vs sensitivity count_ratio={s:.4f} "
        f"diff={diff:.4f} exceeds tolerance {PRIMARY_SENSITIVITY_RATIO_TOL}"
    )


@pytest.mark.slow
def test_primary_and_sensitivity_agree_on_alpha(primary_fit, sensitivity_fit):
    a_p = primary_fit["alpha_mle_nb2"]
    a_s = sensitivity_fit["alpha_mle_nb2"]
    diff = abs(a_p - a_s)
    assert diff < PRIMARY_SENSITIVITY_ALPHA_TOL, (
        f"primary alpha={a_p:.4f} vs sensitivity alpha={a_s:.4f} "
        f"diff={diff:.4f} exceeds tolerance {PRIMARY_SENSITIVITY_ALPHA_TOL}"
    )


# ---------------------------------------------------------------------------
# Truth / output schema
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_truth_values_schema(nb_module, primary_fit, sensitivity_fit):
    values = nb_module.build_truth_values(primary_fit, sensitivity_fit)
    assert len(values) > 0
    for entry in values:
        assert REQUIRED_TRUTH_FIELDS <= set(entry), entry
        assert isinstance(entry["id"], str) and entry["id"]
        assert isinstance(entry["label"], str) and entry["label"]
        assert entry["section"] in {"methods", "results"}, entry
    ids = [v["id"] for v in values]
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"
    must_have = {
        "pref_nb_alpha_nb2", "pref_nb_count_ratio",
        "pref_nb_ci_low", "pref_nb_ci_high", "pref_nb_p",
        "pref_nb_n_clusters_pref", "pref_nb_n_clusters_date",
        "bureau_nb_count_ratio", "bureau_nb_p",
    }
    assert must_have <= set(ids), must_have - set(ids)


@pytest.mark.slow
def test_write_results_roundtrip_rfc8259(nb_module, primary_fit, sensitivity_fit, tmp_path):
    import json

    out = tmp_path / "prefecture_panel_results.json"
    nb_module.write_results(primary_fit, sensitivity_fit, out)
    assert out.exists()

    raw = out.read_text(encoding="utf-8")
    # RFC 8259: NaN is NOT valid JSON. allow_nan=False guarantees we don't emit it.
    assert "NaN" not in raw and "Infinity" not in raw

    doc = json.loads(raw)  # parse; would raise if invalid
    assert doc["project"] == "friday13th"
    assert doc["phase"] == "2C-C2-c"
    assert doc["script"] == "src/02_prefecture_panel_nb.py"
    assert isinstance(doc["values"], list) and doc["values"]
    assert "diagnostics" in doc
    assert "primary_47_prefecture" in doc["diagnostics"]
    assert "sensitivity_51_bureau" in doc["diagnostics"]


def test_v_helper_shape(nb_module):
    entry = nb_module._v("foo", 1.23, "Foo label", "results", ".2f")
    assert entry == {
        "id": "foo", "value": 1.23, "label": "Foo label",
        "section": "results", "format": ".2f",
    }
