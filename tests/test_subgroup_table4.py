"""Unit tests for src/09_subgroup_table4.py (Phase 2C-C5 Table 4).

Verifies:
- All 8 subgroups fit or fall back (never silently drop).
- Fallback path (Poisson GLM) records family='poisson' + fallback_reason.
- Bonferroni threshold is exactly alpha_family / 8.
- Every table row has the manuscript-required cells.
- Descriptive stats match V1 numbers (Fri13 mean 9.9 for fatal, etc.).
- JSON output is native-Python (no numpy leakage).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="module")
def t4_module():
    """Load src/09_subgroup_table4.py (numeric-prefix workaround)."""
    alias = "subgroup_table4"
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(
        alias, SRC_DIR / "09_subgroup_table4.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def all_results(t4_module):
    if not t4_module.SEVERITY_PARQUET.exists():
        pytest.skip(f"missing {t4_module.SEVERITY_PARQUET}")
    return t4_module.run_all_subgroups()


def test_bonferroni_threshold_correct(t4_module):
    assert t4_module.N_SUBGROUPS == 8
    assert t4_module.ALPHA_FAMILY == 0.05
    assert t4_module.BONFERRONI_THRESHOLD == pytest.approx(0.05 / 8)


def test_all_eight_subgroups_produced(all_results):
    assert len(all_results["table4_rows"]) == 8
    keys = {r["subgroup_key"] for r in all_results["table4_rows"]}
    assert keys == {"fatal", "injury", "young", "mid_low", "mid_hi",
                    "elderly", "daytime", "nighttime"}


def test_all_rows_have_manuscript_cells(all_results):
    for r in all_results["table4_rows"]:
        for cell in ("subgroup_label", "n_fri13", "n_other", "mean_fri13",
                     "mean_other", "rr_crude", "p_raw", "p_bonferroni",
                     "nb_converged"):
            assert cell in r, f"row {r.get('subgroup_key')} missing {cell}"


def test_all_have_n_fri13_equal_10(all_results):
    for r in all_results["table4_rows"]:
        assert r["n_fri13"] == 10, (
            f"{r['subgroup_key']}: expected 10 Fri13 rows, got {r['n_fri13']}"
        )


def test_fatal_mean_matches_v1(all_results):
    fatal = next(v for v in all_results["per_subgroup"].values()
                 if v["desc"]["n_fri13"] == 10 and v["desc"]["mean_fri13"] < 20)
    assert fatal["desc"]["mean_fri13"] == pytest.approx(9.9, abs=0.1)
    assert fatal["desc"]["mean_other"] == pytest.approx(7.5, abs=0.3)
    assert fatal["desc"]["rate_ratio_crude"] == pytest.approx(1.31, abs=0.02)


def test_fatal_uses_poisson_fallback(all_results):
    """Fatal counts are small enough (mean ~9.9/day) that NB2 MLE fails on
    BFGS + Nelder-Mead. Verifies we degrade to Poisson honestly."""
    fatal_nb = all_results["per_subgroup"]["fatal"]["nb"]
    assert fatal_nb.get("converged")
    assert fatal_nb.get("family") == "poisson"
    assert fatal_nb.get("fit_method") == "poisson_glm_fallback"
    assert "fallback_reason" in fatal_nb


def test_non_fatal_subgroups_use_nb2(all_results):
    for key in ("injury", "young", "mid_low", "mid_hi", "elderly",
                "daytime", "nighttime"):
        nb = all_results["per_subgroup"][key]["nb"]
        assert nb.get("converged"), f"{key} NB failed unexpectedly"
        assert nb.get("family") == "nb2", (
            f"{key} unexpectedly used {nb.get('family')} instead of NB2"
        )


def test_bonferroni_p_is_min_1(all_results):
    """P values capped at 1.0 after multiplication (0.5 * 8 == 4.0 -> clamp)."""
    for r in all_results["table4_rows"]:
        if r["p_bonferroni"] is not None:
            assert 0 <= r["p_bonferroni"] <= 1.0


def test_fatal_bonferroni_null_survives(all_results):
    """Fatal raw p is ~0.087 (Fri13-only) so Bonferroni x8 = 0.70, well >0.05.
    Locks in the manuscript claim that fatal signal does NOT survive
    Bonferroni once we restrict to Friday-vs-Friday."""
    fatal_row = next(r for r in all_results["table4_rows"]
                      if r["subgroup_key"] == "fatal")
    assert fatal_row["p_bonferroni"] > 0.05


def test_output_is_json_serializable(all_results, t4_module):
    """No numpy leakage after _to_native() pass."""
    native = t4_module._to_native(all_results)
    json.dumps(native)


def test_methods_notes_mentions_bonferroni_and_alpha(all_results):
    notes = all_results["methods_notes"]
    assert "Bonferroni" in notes
    assert "0.05" in notes
    assert "8" in notes
    assert "national-level" in notes
    assert "Figure S3" in notes


def test_values_contain_expected_ids(all_results):
    ids = {v["id"] for v in all_results["values"]}
    for required in (
        "t4_fatal_rr_crude", "t4_fatal_p_raw", "t4_fatal_p_bonferroni",
        "t4_nighttime_rr_crude", "t4_nighttime_nb_count_ratio",
        "t4_n_subgroups", "t4_bonferroni_threshold",
        "t4_n_bonferroni_significant",
    ):
        assert required in ids, f"missing value id: {required}"


def test_merge_truth_absorbs_table4(t4_module):
    """Verify 08_merge_truth.py picks up the JSON we just produced."""
    import importlib.util as iu
    spec = iu.spec_from_file_location("merge_truth", SRC_DIR / "08_merge_truth.py")
    mt = iu.module_from_spec(spec)
    sys.modules["merge_truth"] = mt
    spec.loader.exec_module(mt)
    merged = mt.merge()
    ids = {v["id"] for v in merged["values"]}
    assert "t4_fatal_rr_crude" in ids
    assert "t4_n_bonferroni_significant" in ids
    assert "2C-C5-Table4" in merged["provenance"]
    assert "table4" in merged.get("tables", {})
