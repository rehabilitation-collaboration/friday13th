"""Unit tests for src/number_verification.py (Phase 2C-C5)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"


@pytest.fixture(scope="module")
def nv_module():
    alias = "number_verification"
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(
        alias, SRC_DIR / "number_verification.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def test_render_value_uses_format(nv_module):
    assert nv_module._render_value({"value": 1.048, "format": ".2f"}) == "1.05"
    assert nv_module._render_value({"value": 313, "format": "d"}) == "313"
    assert nv_module._render_value({"value": None, "format": ".2f"}) == "None"


def test_find_numeric_near_matches_within_tolerance(nv_module):
    text = "The count ratio was 1.02 (95% CI: 0.97-1.08, p = 0.36)."
    s, v = nv_module._find_numeric_near(text, target=1.024, tol=0.01)
    assert s == "1.02"
    assert v == pytest.approx(1.02)


def test_find_numeric_near_returns_none_outside_tolerance(nv_module):
    text = "The count ratio was 1.02 (95% CI: 0.97-1.08, p = 0.36)."
    s, v = nv_module._find_numeric_near(text, target=1.50, tol=0.01)
    assert s is None
    assert v is None


def test_find_numeric_near_matches_comma_separated(nv_module):
    text = "We analyzed 1,884,793 police records."
    s, v = nv_module._find_numeric_near(text, target=1884793, tol=0)
    assert v == 1884793


def test_classify_match(nv_module):
    status, note = nv_module._classify(target=1.024, tol=0.005,
                                         found_str="1.02", found_val=1.02)
    assert status == "MATCH"
    assert "≤" in note or "|Δ|" in note


def test_classify_mismatch(nv_module):
    status, note = nv_module._classify(target=1.024, tol=0.001,
                                         found_str="1.02", found_val=1.02)
    assert status == "MISMATCH"


def test_classify_not_found(nv_module):
    status, note = nv_module._classify(target=1.024, tol=0.005,
                                         found_str=None, found_val=None)
    assert status == "NOT_FOUND"


def test_run_produces_report_with_manuscript(nv_module):
    """Integration test — requires manuscript.md + truth.json to exist."""
    if not nv_module.TRUTH_JSON.exists():
        pytest.skip("truth.json missing")
    if not nv_module.MANUSCRIPT_MD.exists():
        pytest.skip("manuscript.md missing")
    report = nv_module.run()
    assert "results" in report
    assert "counts" in report
    assert "pass" in report
    assert report["n_checks"] == len(report["results"])
    assert report["n_checks"] >= 40  # CORE_CHECKS length lower bound


def test_all_manuscript_facing_numbers_pass(nv_module):
    """Fail loudly if C5 manuscript integration missed a number.

    This is the M3-submission gate: if any core check MISMATCHes or is
    missing from truth.json, pytest turns red before we regenerate the PDF."""
    if not nv_module.TRUTH_JSON.exists() or not nv_module.MANUSCRIPT_MD.exists():
        pytest.skip("truth.json or manuscript.md missing")
    report = nv_module.run()
    problems = [
        r for r in report["results"]
        if r["status"] in ("MISMATCH", "TRUTH_MISSING")
    ]
    assert not problems, (
        f"{len(problems)} manuscript numbers failed verification: "
        + ", ".join(f"{p['id']}({p['status']})" for p in problems[:10])
    )


def test_render_markdown_contains_summary(nv_module):
    if not nv_module.TRUTH_JSON.exists() or not nv_module.MANUSCRIPT_MD.exists():
        pytest.skip("truth.json or manuscript.md missing")
    report = nv_module.run()
    md = nv_module.render_markdown(report)
    assert "Number verification" in md
    assert "Status counts" in md
    assert "Per-check detail" in md
    for r in report["results"][:3]:
        assert r["id"] in md


def test_json_serializable(nv_module):
    if not nv_module.TRUTH_JSON.exists() or not nv_module.MANUSCRIPT_MD.exists():
        pytest.skip("truth.json or manuscript.md missing")
    report = nv_module.run()
    json.dumps(report)
