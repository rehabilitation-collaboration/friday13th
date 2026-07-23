"""Phase 2C-C5: merge V1 truth.json base with Phase 2C JSON outputs.

Reads:
  - output/truth.json                          (V1 base, 80 values, 2026-03-27)
  - output/prefecture_panel_results.json       (2C-c, 22 values, pref_nb_/bureau_nb_)
  - output/weather_holiday_nb_results.json     (2C-e, 23 values, pref_nb_wh_/bureau_nb_wh_)
  - output/diagnostics_results.json            (2C-C1, extract from diagnostics/*)
  - output/case_crossover_results.json         (2C-C3, extract from conditional_poisson/exact_sign/permutation)
  - output/prefecture_irr_by_prefecture.json   (2C-C4, 12 values, pref_by_pref_)
  - output/subgroup_table4_results.json        (2C-C5 Table 4, if exists)

Writes:
  - output/truth.json                          (unified V2 source-of-truth for manuscript verification)

Design (2C-C5 PLAN-DEVIATIONS #2):
Original PLAN said "extend 02_main_analysis.py --export-truth". We instead
build a new merge script to (a) preserve V1 base without touching the
V1 main-analysis pipeline (single-responsibility) and (b) provide a
re-runnable stitch layer for round 2/3/4... additional JSONs.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"

BASE_TRUTH = OUTPUT_DIR / "truth.json"
PREF_PANEL = OUTPUT_DIR / "prefecture_panel_results.json"
WEATHER_NB = OUTPUT_DIR / "weather_holiday_nb_results.json"
DIAGNOSTICS = OUTPUT_DIR / "diagnostics_results.json"
CASE_CROSSOVER = OUTPUT_DIR / "case_crossover_results.json"
PREF_BY_PREF = OUTPUT_DIR / "prefecture_irr_by_prefecture.json"
SUBGROUP_T4 = OUTPUT_DIR / "subgroup_table4_results.json"


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


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_c1(diag_json: dict) -> list[dict]:
    """Extract Phase 2C-C1 diagnostics values (03_primary focus).

    We take 03_primary (the manuscript-facing primary spec) as the values
    to embed in truth.json; other specs remain in the source JSON for audit.
    """
    out: list[dict] = []
    diag = diag_json.get("diagnostics", {})

    def _find(items: list[dict], label: str) -> dict:
        for it in items:
            if it.get("spec_label") == label:
                return it
        return {}

    disp = _find(diag.get("dispersion", []), "03_primary")
    if disp:
        out += [
            _v("diag_alpha_nb2", disp.get("alpha_nb2"),
               "2C-C1 dispersion alpha (NB2) for 03_primary",
               "results", ".4f"),
            _v("diag_alpha_nb1", disp.get("alpha_nb1"),
               "2C-C1 dispersion alpha (NB1) for 03_primary",
               "results", ".3f"),
            _v("diag_count_ratio_nb2", disp.get("count_ratio_nb2"),
               "2C-C1 03_primary NB2 count ratio (dispersion diagnostic)",
               "results", ".4f"),
            _v("diag_count_ratio_nb1", disp.get("count_ratio_nb1"),
               "2C-C1 03_primary NB1 count ratio (parameterization robustness)",
               "results", ".4f"),
            _v("diag_count_ratio_abs_delta_nb2_vs_nb1",
               disp.get("count_ratio_abs_diff_nb2_vs_nb1"),
               "2C-C1 |NB2 - NB1| count-ratio delta (spec robustness)",
               "results", ".4f"),
        ]

    pearson = _find(diag.get("pearson_residuals", []), "03_primary")
    if pearson:
        out += [
            _v("diag_pearson_n", pearson.get("n"),
               "2C-C1 Pearson residuals N (03_primary)", "results", "d"),
            _v("diag_pearson_mean", pearson.get("mean"),
               "2C-C1 Pearson residuals mean (03_primary)",
               "results", ".3f"),
            _v("diag_pearson_sd", pearson.get("sd"),
               "2C-C1 Pearson residuals SD (03_primary)",
               "results", ".3f"),
            _v("diag_pearson_prop_abs_gt_2", pearson.get("prop_abs_gt_2"),
               "2C-C1 Pearson |r|>2 proportion (03_primary)",
               "results", ".4f"),
            _v("diag_pearson_prop_abs_gt_3", pearson.get("prop_abs_gt_3"),
               "2C-C1 Pearson |r|>3 proportion (03_primary)",
               "results", ".4f"),
        ]

    qp = _find(diag.get("quasi_poisson", []), "03_primary")
    if qp:
        out += [
            _v("diag_qp_scale_factor", qp.get("scale_factor"),
               "2C-C1 Quasi-Poisson scale factor (03_primary)",
               "results", ".3f"),
            _v("diag_qp_count_ratio", qp.get("count_ratio"),
               "2C-C1 Quasi-Poisson count ratio (03_primary)",
               "results", ".4f"),
            _v("diag_qp_se_cluster_2way", qp.get("is_fri13_se_cluster_2way"),
               "2C-C1 Quasi-Poisson two-way cluster SE (03_primary)",
               "results", ".4f"),
        ]

    hc1 = _find(diag.get("hc1_robust_se", []), "03_primary")
    if hc1:
        out += [
            _v("diag_hc1_se", hc1.get("is_fri13_se_hc1"),
               "2C-C1 HC1 heteroscedasticity-robust SE (03_primary)",
               "results", ".4f"),
            _v("diag_hc1_se_iid", hc1.get("is_fri13_se_iid"),
               "2C-C1 iid SE (03_primary)", "results", ".4f"),
            _v("diag_hc1_se_cluster_2way", hc1.get("is_fri13_se_cluster_2way"),
               "2C-C1 two-way cluster SE (03_primary)", "results", ".4f"),
            _v("diag_hc1_over_cluster_ratio",
               hc1.get("hc1_over_cluster_2way_ratio"),
               "2C-C1 HC1/cluster SE ratio (03_primary)",
               "results", ".3f"),
        ]

    spec = _find(diag.get("spec_sensitivity", []), "03_primary")
    if spec:
        deltas = spec.get("abs_count_ratio_delta_vs_dummy", {})
        out.append(_v(
            "diag_spec_max_abs_ratio_delta",
            spec.get("max_abs_count_ratio_delta_vs_dummy"),
            "2C-C1 max |count-ratio delta| across seasonality specs (03_primary)",
            "results", ".4f",
        ))
        if deltas.get("harmonic") is not None:
            out.append(_v(
                "diag_spec_harmonic_delta", deltas["harmonic"],
                "2C-C1 harmonic vs dummy |count-ratio delta| (03_primary)",
                "results", ".4f",
            ))

    boot = _find(diag.get("pair_cluster_boot_pref_only", []), "03_primary")
    if boot:
        out += [
            _v("diag_boot_ci_low", boot.get("count_ratio_ci_low_boot"),
               "2C-C1 pair-cluster bootstrap 95% CI lower (03_primary)",
               "results", ".4f"),
            _v("diag_boot_ci_high", boot.get("count_ratio_ci_high_boot"),
               "2C-C1 pair-cluster bootstrap 95% CI upper (03_primary)",
               "results", ".4f"),
            _v("diag_boot_p", boot.get("p_two_sided_boot"),
               "2C-C1 pair-cluster bootstrap two-sided p (03_primary)",
               "results", ".3f"),
            _v("diag_boot_n_iter", boot.get("n_iter_successful"),
               "2C-C1 bootstrap iterations successful (03_primary)",
               "methods", "d"),
            _v("diag_boot_conv_failures", boot.get("convergence_failures"),
               "2C-C1 bootstrap convergence failures (03_primary)",
               "methods", "d"),
        ]
    return out


def _extract_c3(cc_json: dict) -> list[dict]:
    """Extract Phase 2C-C3 case-crossover values.

    Old truth.json V1 already has cc_mean_ratio/cc_t/cc_p from the
    superseded arithmetic t-test. We prefix new values with `cc_new_`
    to keep both visible (V1 audit + V2 primary) — the V2 manuscript
    references only cc_new_* per methods_draft_c3.notes[] entry 1(b).
    """
    out: list[dict] = []
    cp = cc_json.get("conditional_poisson", {})
    sign = cc_json.get("exact_sign", {})
    perm = cc_json.get("permutation", {})
    cfg = cc_json.get("config", {})

    if cp:
        out += [
            _v("cc_new_beta_mle", cp.get("beta"),
               "2C-C3 conditional-Poisson MLE beta", "results", ".4f"),
            _v("cc_new_count_ratio", cp.get("count_ratio"),
               "2C-C3 conditional-Poisson MLE count ratio", "results", ".4f"),
            _v("cc_new_n_strata", cp.get("n_strata"),
               "2C-C3 conditional-Poisson N strata (G clusters)",
               "methods", "d"),
            _v("cc_new_n_iter_nr", cp.get("n_iter"),
               "2C-C3 conditional-Poisson Newton-Raphson iterations",
               "methods", "d"),
        ]
        small_g = cp.get("small_G_correction", {})
        if small_g:
            out += [
                _v("cc_new_small_g_factor",
                   small_g.get("finite_cluster_correction_factor"),
                   "2C-C3 Cameron-Miller finite-cluster factor G/(G-1)",
                   "methods", ".4f"),
                _v("cc_new_t_crit_g_minus_1", small_g.get("t_crit_95_df"),
                   "2C-C3 t critical value at df=G-1", "methods", ".3f"),
            ]
        sw_t = cp.get("sandwich_cluster_t", {})
        sw_z = cp.get("sandwich_cluster_z", {})
        if sw_t:
            out += [
                _v("cc_new_sw_t_se", sw_t.get("se_beta"),
                   "2C-C3 sandwich cluster SE (primary reporting)",
                   "results", ".4f"),
                _v("cc_new_sw_t_ci_low", sw_t.get("count_ratio_ci_low"),
                   "2C-C3 sandwich-t(G-1) 95% CI lower (primary)",
                   "results", ".4f"),
                _v("cc_new_sw_t_ci_high", sw_t.get("count_ratio_ci_high"),
                   "2C-C3 sandwich-t(G-1) 95% CI upper (primary)",
                   "results", ".4f"),
                _v("cc_new_sw_t_p", sw_t.get("p_two_sided"),
                   "2C-C3 sandwich-t(G-1) two-sided p (primary)",
                   "results", ".3f"),
            ]
        if sw_z:
            out += [
                _v("cc_new_sw_z_ci_low", sw_z.get("count_ratio_ci_low"),
                   "2C-C3 sandwich-z 95% CI lower (sensitivity)",
                   "results", ".4f"),
                _v("cc_new_sw_z_ci_high", sw_z.get("count_ratio_ci_high"),
                   "2C-C3 sandwich-z 95% CI upper (sensitivity)",
                   "results", ".4f"),
                _v("cc_new_sw_z_p", sw_z.get("p_two_sided"),
                   "2C-C3 sandwich-z two-sided p (sensitivity)",
                   "results", ".3f"),
            ]

    if sign:
        out += [
            _v("cc_new_sign_n_plus", sign.get("n_plus"),
               "2C-C3 exact sign test n+ (Fri13 higher)", "results", "d"),
            _v("cc_new_sign_n_minus", sign.get("n_minus"),
               "2C-C3 exact sign test n- (control higher)", "results", "d"),
            _v("cc_new_sign_n_zero", sign.get("n_zero"),
               "2C-C3 exact sign test ties", "results", "d"),
            _v("cc_new_sign_p", sign.get("p_two_sided"),
               "2C-C3 exact sign test two-sided p", "results", ".3f"),
        ]

    if perm:
        out += [
            _v("cc_new_perm_geo_ratio", perm.get("observed_geometric_ratio"),
               "2C-C3 permutation observed geometric count ratio",
               "results", ".4f"),
            _v("cc_new_perm_mean_log_ratio",
               perm.get("observed_mean_log_ratio"),
               "2C-C3 permutation observed mean log-ratio",
               "results", ".4f"),
        ]
        ee = perm.get("exact_enumeration", {})
        mc = perm.get("monte_carlo", {})
        if ee:
            out += [
                _v("cc_new_perm_exact_p", ee.get("p_two_sided"),
                   "2C-C3 permutation exact two-sided p (2^10 enumeration)",
                   "results", ".4f"),
                _v("cc_new_perm_n_patterns", ee.get("n_sign_patterns"),
                   "2C-C3 permutation N enumerated patterns",
                   "methods", "d"),
            ]
        if mc:
            out += [
                _v("cc_new_perm_mc_p", mc.get("p_two_sided"),
                   "2C-C3 permutation Monte-Carlo two-sided p",
                   "results", ".4f"),
                _v("cc_new_perm_mc_se", mc.get("mc_se_p"),
                   "2C-C3 permutation Monte-Carlo SE",
                   "results", ".4f"),
                _v("cc_new_perm_mc_n", mc.get("n_perm"),
                   "2C-C3 permutation Monte-Carlo iterations",
                   "methods", "d"),
            ]

    if cfg:
        out.append(_v("cc_new_z_crit_95", cfg.get("z_crit_95"),
                      "2C-C3 z_{0.975} critical value (scipy full precision)",
                      "methods", ".6f"))
    return out


def _to_native(obj: Any) -> Any:
    """Numpy → Python native, ensure JSON-serializable."""
    try:
        import numpy as np  # noqa: WPS433
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except Exception:  # numpy optional
        pass
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    return obj


def merge() -> dict:
    base = _load(BASE_TRUTH) or {
        "project": "friday13th",
        "generated": "unknown",
        "script": "src/02_main_analysis.py",
        "values": [],
        "tables": {},
    }

    values: list[dict] = list(base.get("values", []))
    tables: dict = dict(base.get("tables", {}))

    provenance: dict[str, str] = {"base": str(BASE_TRUTH.name)}

    for path, prefix_hint in (
        (PREF_PANEL, "2C-c"),
        (WEATHER_NB, "2C-e"),
        (PREF_BY_PREF, "2C-C4"),
    ):
        js = _load(path)
        if not js:
            print(f"[WARN] {path.name} not found, skipping {prefix_hint}",
                  file=sys.stderr)
            continue
        vals = js.get("values", [])
        values.extend(vals)
        provenance[prefix_hint] = path.name

    diag_js = _load(DIAGNOSTICS)
    if diag_js:
        values.extend(_extract_c1(diag_js))
        provenance["2C-C1"] = DIAGNOSTICS.name

    cc_js = _load(CASE_CROSSOVER)
    if cc_js:
        values.extend(_extract_c3(cc_js))
        provenance["2C-C3"] = CASE_CROSSOVER.name

    t4_js = _load(SUBGROUP_T4)
    if t4_js:
        values.extend(t4_js.get("values", []))
        rows = t4_js.get("table4_rows")
        if rows:
            tables["table4"] = rows
        provenance["2C-C5-Table4"] = SUBGROUP_T4.name

    seen: dict[str, int] = {}
    deduped: list[dict] = []
    dup_ids: list[str] = []
    for v in values:
        vid = v.get("id")
        if not vid:
            continue
        if vid in seen:
            dup_ids.append(vid)
            deduped[seen[vid]] = v
        else:
            seen[vid] = len(deduped)
            deduped.append(v)

    merged = {
        "project": "friday13th",
        "phase": "2C-C5",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "src/08_merge_truth.py",
        "provenance": provenance,
        "n_values": len(deduped),
        "n_duplicate_ids_overwritten": len(dup_ids),
        "values": deduped,
        "tables": tables,
    }

    merged = _to_native(merged)
    return merged


def main() -> None:
    merged = merge()
    BASE_TRUTH.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    n_v = merged["n_values"]
    n_dup = merged["n_duplicate_ids_overwritten"]
    provenance = merged["provenance"]
    print(f"[OK] {BASE_TRUTH} written: {n_v} values (dup overwritten: {n_dup})")
    print(f"[OK] provenance: {provenance}")


if __name__ == "__main__":
    main()
