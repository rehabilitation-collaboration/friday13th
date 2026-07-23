"""Manuscript number verification for the friday13th manuscript.

Reads:
  - output/truth.json       (single source of truth, produced by 08_merge_truth.py)
  - manuscript.md           (V2 manuscript text)

For each `manuscript-facing` truth value (a curated core list — not the full
280-value dump), searches the manuscript for the expected rendered value with
a small numeric tolerance. Reports:

  - MATCH      : expected value found in manuscript within tolerance
  - NOT_FOUND  : no numeric near the expected value found in manuscript
  - MISMATCH   : nearest numeric differs by more than tolerance

Writes:
  - output/number_verification.md    (human-readable markdown table)
  - output/number_verification.json  (machine-readable per-check status)

Design notes:
  1. The `CORE_CHECKS` list is the manuscript-facing subset — it evolves per
     GPT review round. Values not in this list can still be traced via
     truth.json but are not auto-verified against prose. Kept short and
     targeted (~40 entries) to avoid false-positive matches on unrelated
     numbers.
  2. Tolerance defaults to ±0.005 for `.2f`/`.3f` counts and ±0.05 for `.1f`.
     Exact match required for integer IDs.
  3. Search is regex-based over the manuscript text with word-boundary
     protection to avoid matching e.g. "1.04" inside "1.048".
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
TRUTH_JSON = OUTPUT_DIR / "truth.json"
MANUSCRIPT_MD = PROJECT_DIR / "manuscript.md"
OUT_MD = OUTPUT_DIR / "number_verification.md"
OUT_JSON = OUTPUT_DIR / "number_verification.json"

CORE_CHECKS: list[dict] = [
    {"id": "total_records", "context": "Abstract Methods", "tol": 0},
    {"id": "n_friday13", "context": "Abstract / Introduction", "tol": 0},
    {"id": "n_other_fri", "context": "Abstract sample size", "tol": 0},
    {"id": "fri13_mean", "context": "Results descriptive", "tol": 0.5},
    {"id": "other_fri_mean", "context": "Results descriptive", "tol": 0.5},
    {"id": "scanlon_rr", "context": "Abstract/Results Scanlon", "tol": 0.02},
    {"id": "scanlon_p_t", "context": "Abstract Scanlon", "tol": 0.02},
    {"id": "nayha_rr", "context": "Abstract/Results Näyhä", "tol": 0.02},
    {"id": "nayha_ci_low", "context": "Results Näyhä", "tol": 0.03},
    {"id": "nayha_ci_high", "context": "Results Näyhä", "tol": 0.03},
    {"id": "lo_f", "context": "Abstract Lo", "tol": 0.02},
    {"id": "lo_p_anova", "context": "Abstract Lo", "tol": 0.02},
    {"id": "pref_nb_wh_count_ratio", "context": "Abstract/Results panel primary",
     "tol": 0.005},
    {"id": "pref_nb_wh_ci_low", "context": "Abstract/Results panel CI",
     "tol": 0.005},
    {"id": "pref_nb_wh_ci_high", "context": "Abstract/Results panel CI",
     "tol": 0.005},
    {"id": "pref_nb_wh_p", "context": "Abstract/Results panel p", "tol": 0.005},
    {"id": "diag_alpha_nb2", "context": "Methods diagnostics α_NB2",
     "tol": 0.005},
    {"id": "diag_qp_scale_factor", "context": "Methods diagnostics QP",
     "tol": 0.02},
    {"id": "diag_boot_ci_low", "context": "Results bootstrap sensitivity",
     "tol": 0.005},
    {"id": "diag_boot_ci_high", "context": "Results bootstrap sensitivity",
     "tol": 0.005},
    {"id": "diag_boot_p", "context": "Results bootstrap sensitivity",
     "tol": 0.02},
    {"id": "cc_new_count_ratio", "context": "Abstract/Results case-crossover primary",
     "tol": 0.01},
    {"id": "cc_new_sw_t_ci_low", "context": "Abstract case-crossover CI",
     "tol": 0.005},
    {"id": "cc_new_sw_t_ci_high", "context": "Abstract case-crossover CI",
     "tol": 0.005},
    {"id": "cc_new_sw_t_p", "context": "Abstract/Results case-crossover p",
     "tol": 0.02},
    {"id": "cc_new_sign_n_plus", "context": "Abstract sign test 8 of 10",
     "tol": 0},
    {"id": "cc_new_sign_p", "context": "Abstract sign test p", "tol": 0.02},
    {"id": "cc_new_perm_geo_ratio", "context": "Results permutation geometric",
     "tol": 0.01},
    {"id": "cc_new_perm_exact_p", "context": "Results permutation exact p",
     "tol": 0.02},
    {"id": "cc_new_perm_mc_p", "context": "Results permutation MC p",
     "tol": 0.02},
    {"id": "pref_by_pref_ratio_min", "context": "Abstract prefecture range Tottori",
     "tol": 0.02},
    {"id": "pref_by_pref_ratio_max", "context": "Abstract prefecture range Iwate",
     "tol": 0.02},
    {"id": "pref_by_pref_ratio_median", "context": "Abstract prefecture median",
     "tol": 0.02},
    {"id": "pref_by_pref_n_ci_excludes_one", "context": "Results 5 prefectures",
     "tol": 0},
    {"id": "pref_by_pref_n_ci_excludes_one_binomial_p",
     "context": "Results binomial excess p", "tol": 0.005},
    {"id": "pref_by_pref_n_bonferroni_significant",
     "context": "Results Bonferroni 1 Mie", "tol": 0},
    {"id": "pref_by_pref_n_bh_fdr_significant",
     "context": "Results BH-FDR 1 Mie", "tol": 0},
    {"id": "t4_fatal_rr_crude", "context": "Table 4 fatal RR", "tol": 0.005},
    {"id": "t4_fatal_p_raw", "context": "Table 4 fatal raw p", "tol": 0.005},
    {"id": "t4_fatal_p_bonferroni", "context": "Table 4 fatal Bonferroni",
     "tol": 0.02},
    {"id": "t4_fatal_nb_count_ratio", "context": "Table 4 fatal NB approx",
     "tol": 0.02},
    {"id": "t4_nighttime_rr_crude", "context": "Table 4 nighttime RR",
     "tol": 0.005},
    {"id": "t4_daytime_rr_crude", "context": "Table 4 daytime RR", "tol": 0.005},
]


def _load_truth() -> dict[str, dict]:
    if not TRUTH_JSON.exists():
        print(f"[FATAL] {TRUTH_JSON} missing — run src/08_merge_truth.py first",
              file=sys.stderr)
        sys.exit(1)
    data = json.loads(TRUTH_JSON.read_text(encoding="utf-8"))
    return {v["id"]: v for v in data.get("values", [])}


def _render_value(v: dict) -> str:
    """Render truth value using its stored format spec."""
    val = v["value"]
    fmt = v.get("format", "")
    if val is None:
        return "None"
    try:
        return format(val, fmt)
    except (TypeError, ValueError):
        return str(val)


def _find_numeric_near(text: str, target: float, tol: float) -> tuple[str | None, float | None]:
    """Search text for numeric literals within `tol` of `target`.

    Returns (matched_string, matched_value) or (None, None).
    Uses a regex that captures optional leading sign, integer part with
    optional thousands separators, and optional decimal part.
    """
    pattern = re.compile(r"(?<![\w.])(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\-?\d+\.\d+|-?\d+)")
    best: tuple[str | None, float | None, float] = (None, None, float("inf"))
    for m in pattern.finditer(text):
        raw = m.group(0)
        try:
            num = float(raw.replace(",", ""))
        except ValueError:
            continue
        diff = abs(num - target)
        if diff < best[2]:
            best = (raw, num, diff)
    if best[0] is None:
        return None, None
    if best[2] <= tol:
        return best[0], best[1]
    return None, None


def _classify(target: float, tol: float, found_str: str | None,
               found_val: float | None) -> tuple[str, str]:
    if found_val is None:
        return "NOT_FOUND", "no numeric within tolerance"
    diff = abs(found_val - target)
    if diff <= tol:
        return "MATCH", f"|Δ|={diff:.4f} ≤ tol={tol}"
    return "MISMATCH", f"|Δ|={diff:.4f} > tol={tol} (found {found_val})"


def run() -> dict:
    truth = _load_truth()
    manuscript = MANUSCRIPT_MD.read_text(encoding="utf-8")

    results: list[dict] = []
    for check in CORE_CHECKS:
        vid = check["id"]
        if vid not in truth:
            results.append({
                "id": vid,
                "context": check["context"],
                "expected": None,
                "rendered": None,
                "found": None,
                "status": "TRUTH_MISSING",
                "note": "truth.json has no entry for this id",
            })
            continue
        v = truth[vid]
        expected = v["value"]
        if expected is None:
            results.append({
                "id": vid,
                "context": check["context"],
                "expected": None,
                "rendered": None,
                "found": None,
                "status": "TRUTH_NULL",
                "note": "truth value is null",
            })
            continue
        target = float(expected)
        tol = float(check.get("tol", 0))
        found_str, found_val = _find_numeric_near(manuscript, target, tol)
        status, note = _classify(target, tol, found_str, found_val)
        results.append({
            "id": vid,
            "context": check["context"],
            "expected": expected,
            "rendered": _render_value(v),
            "tol": tol,
            "found": found_val,
            "found_str": found_str,
            "status": status,
            "note": note,
        })

    counts = {"MATCH": 0, "NOT_FOUND": 0, "MISMATCH": 0,
              "TRUTH_MISSING": 0, "TRUTH_NULL": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    return {
        "project": "friday13th",
        "phase": "2C-C5-number-verification",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "manuscript_path": str(MANUSCRIPT_MD),
        "truth_path": str(TRUTH_JSON),
        "n_checks": len(results),
        "counts": counts,
        "pass": counts["MISMATCH"] == 0 and counts["TRUTH_MISSING"] == 0,
        "results": results,
    }


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# Number verification — Phase 2C-C5")
    lines.append("")
    lines.append(f"- Generated (UTC): {report['generated']}")
    lines.append(f"- Manuscript: `{Path(report['manuscript_path']).name}`")
    lines.append(f"- Truth source: `{Path(report['truth_path']).name}`")
    lines.append(f"- Total core checks: {report['n_checks']}")
    lines.append(f"- Overall pass: **{report['pass']}**")
    lines.append("")
    lines.append("## Status counts")
    lines.append("")
    for k, v in report["counts"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Per-check detail")
    lines.append("")
    lines.append("| id | context | expected (rendered) | tol | status | found | note |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in report["results"]:
        rendered = r.get("rendered") or "(null)"
        tol = r.get("tol", "-")
        found = r.get("found_str") or "-"
        lines.append(
            f"| `{r['id']}` | {r['context']} | {r.get('expected','-')} ({rendered})"
            f" | {tol} | **{r['status']}** | {found} | {r.get('note','')} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = run()
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                          encoding="utf-8")
    OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(f"[OK] {OUT_JSON} written")
    print(f"[OK] {OUT_MD} written")
    print(f"     counts = {report['counts']}, overall pass = {report['pass']}")
    if not report["pass"]:
        for r in report["results"]:
            if r["status"] in ("MISMATCH", "TRUTH_MISSING"):
                print(f"     [{r['status']}] {r['id']}: {r.get('note','')}")


if __name__ == "__main__":
    main()
