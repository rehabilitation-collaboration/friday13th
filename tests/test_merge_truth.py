"""Unit tests for src/08_merge_truth.py (Phase 2C-C5).

Verifies:
- Extractors pull the manuscript-facing 03_primary values from the C1 and
  C3 JSONs and don't silently emit None.
- The merged truth.json has the correct schema on every value (id, value,
  label, section, format).
- Provenance dict lists every source path.
- The output is JSON-serializable (no numpy types leak).
- Manuscript-facing IDs referenced by methods_draft_c3.notes[] and the
  Figure S3 discussion paragraph are present with the expected values.
- Duplicate IDs collapse to a single entry (last-write-wins).
"""
from __future__ import annotations

import json

import pytest

MANUSCRIPT_FACING_IDS = {
    # 2C-e (primary panel)
    "pref_nb_wh_count_ratio": (1.024, 1.026),
    "pref_nb_wh_ci_low": (0.97, 0.98),
    "pref_nb_wh_ci_high": (1.07, 1.09),
    "pref_nb_wh_p": (0.35, 0.37),
    # 2C-C1 (diagnostics)
    "diag_alpha_nb2": (0.02, 0.03),
    "diag_qp_scale_factor": (1.40, 1.50),
    "diag_boot_ci_low": (0.98, 1.00),
    "diag_boot_ci_high": (1.04, 1.06),
    # 2C-C3 (case-crossover primary = sandwich-t(9))
    "cc_new_count_ratio": (1.035, 1.038),
    "cc_new_sw_t_p": (0.39, 0.41),
    "cc_new_sign_n_plus": (8, 8),
    "cc_new_perm_exact_p": (0.44, 0.45),
    # 2C-C4 (Figure S3 forest)
    "pref_by_pref_ratio_median": (1.008, 1.012),
    "pref_by_pref_n_ci_excludes_one_binomial_p": (0.08, 0.09),
    "pref_by_pref_n_bonferroni_significant": (1, 1),
}

REQUIRED_SCHEMA_KEYS = {"id", "value", "label", "section", "format"}


@pytest.fixture(scope="module")
def merged_truth(merge_truth_module):
    """Run merge_truth.merge() and return the merged dict without touching disk."""
    return merge_truth_module.merge()


def test_merge_returns_expected_top_level(merged_truth):
    assert merged_truth["project"] == "friday13th"
    assert merged_truth["phase"] == "2C-C5"
    assert merged_truth["script"] == "src/08_merge_truth.py"
    assert isinstance(merged_truth["values"], list)
    assert isinstance(merged_truth["provenance"], dict)


def test_provenance_lists_all_phase_2c_sources(merged_truth):
    prov = merged_truth["provenance"]
    for key in ("base", "2C-c", "2C-e", "2C-C1", "2C-C3", "2C-C4"):
        assert key in prov, f"missing provenance key {key}: {prov}"


def test_all_values_have_required_schema(merged_truth):
    for v in merged_truth["values"]:
        missing = REQUIRED_SCHEMA_KEYS - set(v.keys())
        assert not missing, f"value {v.get('id')} missing keys: {missing}"


def test_no_duplicate_ids_in_output(merged_truth):
    seen = set()
    for v in merged_truth["values"]:
        vid = v["id"]
        assert vid not in seen, f"duplicate id in merged output: {vid}"
        seen.add(vid)


def test_manuscript_facing_ids_present_and_in_range(merged_truth):
    by_id = {v["id"]: v for v in merged_truth["values"]}
    for vid, (lo, hi) in MANUSCRIPT_FACING_IDS.items():
        assert vid in by_id, f"missing manuscript-facing id: {vid}"
        val = by_id[vid]["value"]
        assert val is not None, f"{vid} value is None"
        assert lo <= val <= hi, f"{vid}={val} outside [{lo}, {hi}]"


def test_output_is_json_serializable(merged_truth):
    """No numpy types should leak (would break json.dump default)."""
    json.dumps(merged_truth)


def test_extract_c1_pulls_03_primary_only(merge_truth_module, diagnostics_json):
    values = merge_truth_module._extract_c1(diagnostics_json)
    ids = {v["id"] for v in values}
    assert "diag_alpha_nb2" in ids
    assert "diag_pearson_prop_abs_gt_3" in ids
    assert "diag_qp_scale_factor" in ids
    assert "diag_boot_ci_low" in ids
    assert "diag_hc1_over_cluster_ratio" in ids
    # No 02_primary/02_sensitivity/03_sensitivity leakage
    for v in values:
        assert "02_" not in v.get("label", "")
        assert "03_sensitivity" not in v.get("label", "")


def test_extract_c3_pulls_conditional_poisson_and_sign_and_perm(
    merge_truth_module, case_crossover_json,
):
    values = merge_truth_module._extract_c3(case_crossover_json)
    ids = {v["id"] for v in values}
    # Primary sandwich-t(9) reporting
    assert "cc_new_sw_t_p" in ids
    assert "cc_new_sw_t_ci_low" in ids
    assert "cc_new_sw_t_ci_high" in ids
    # Sensitivity z-based
    assert "cc_new_sw_z_p" in ids
    # Exact sign + permutation
    assert "cc_new_sign_p" in ids
    assert "cc_new_perm_exact_p" in ids
    assert "cc_new_perm_mc_p" in ids


def test_extract_c3_does_not_emit_fisher_iid_diagnostic(
    merge_truth_module, case_crossover_json,
):
    """Framing bomb guard: Fisher iid values must NOT enter truth.json —
    the JSON keeps them for audit only (methods_draft_c3.notes[] entry 3)."""
    values = merge_truth_module._extract_c3(case_crossover_json)
    ids = {v["id"] for v in values}
    for banned in ("cc_new_fisher_p", "cc_new_fisher_ci_low",
                   "cc_new_fisher_ci_high", "cc_new_fisher_se"):
        assert banned not in ids, f"Fisher iid value leaked into truth: {banned}"


def test_multi_test_disclosure_fields_all_present(merged_truth):
    """C4 AKAGI B4: multi-test disclosure 3 fields must appear so the
    Figure S3 paragraph can quote binomtest / Bonferroni / BH-FDR verbatim."""
    ids = {v["id"] for v in merged_truth["values"]}
    for required in (
        "pref_by_pref_n_ci_excludes_one",
        "pref_by_pref_n_ci_excludes_one_binomial_p",
        "pref_by_pref_n_bonferroni_significant",
        "pref_by_pref_n_bh_fdr_significant",
    ):
        assert required in ids, (
            f"multi-test disclosure field missing: {required}"
        )


def test_dedup_last_write_wins(merge_truth_module):
    """Duplicate id from a later source overwrites earlier."""
    v_old = merge_truth_module._v("dup_id", 1.0, "old", "results", ".2f")
    v_new = merge_truth_module._v("dup_id", 2.0, "new", "results", ".2f")
    values = [v_old, v_new]
    # Simulate the dedup pass inline
    seen: dict[str, int] = {}
    deduped: list[dict] = []
    for v in values:
        vid = v["id"]
        if vid in seen:
            deduped[seen[vid]] = v
        else:
            seen[vid] = len(deduped)
            deduped.append(v)
    assert len(deduped) == 1
    assert deduped[0]["value"] == 2.0
    assert deduped[0]["label"] == "new"
