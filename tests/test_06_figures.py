"""Smoke tests for src/06_figures.py (Phase 2C-C4).

Coverage:
  - argparse CLI (choices validation, --only flag)
  - .exists() guard for missing input JSONs (no crash, graceful skip)
  - S2 / S3 make_figure_* end-to-end (PNG produced, non-empty)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"


@pytest.fixture(scope="session")
def figures_module():
    """Load src/06_figures.py under an importable alias."""
    if "figures_module" in sys.modules:
        return sys.modules["figures_module"]
    spec = importlib.util.spec_from_file_location(
        "figures_module", SRC_DIR / "06_figures.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["figures_module"] = module
    spec.loader.exec_module(module)
    return module


def test_parse_args_default(figures_module):
    args = figures_module.parse_args([])
    assert args.only == "all"


def test_parse_args_only_s2(figures_module):
    args = figures_module.parse_args(["--only", "s2"])
    assert args.only == "s2"


def test_parse_args_rejects_invalid_choice(figures_module):
    """argparse choices validation must reject typos (was silently no-op in v1)."""
    with pytest.raises(SystemExit):
        figures_module.parse_args(["--only", "S2"])  # case-sensitive


def test_parse_args_rejects_unknown_flag(figures_module):
    with pytest.raises(SystemExit):
        figures_module.parse_args(["--foo"])


def test_make_figure_s2_missing_json_skips(figures_module, monkeypatch, tmp_path, capsys):
    """When the upstream case_crossover JSON is absent, S2 must skip cleanly
    (return None + print), not raise FileNotFoundError."""
    monkeypatch.setattr(figures_module, "CASE_CROSSOVER_JSON", tmp_path / "missing.json")
    result = figures_module.make_figure_s2()
    assert result is None
    captured = capsys.readouterr()
    assert "SKIPPED" in captured.out


def test_make_figure_s3_missing_json_skips(figures_module, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(figures_module, "PREF_IRR_JSON", tmp_path / "missing.json")
    result = figures_module.make_figure_s3()
    assert result is None
    captured = capsys.readouterr()
    assert "SKIPPED" in captured.out


def test_make_figure_s2_writes_png(figures_module, tmp_path, monkeypatch):
    if not figures_module.CASE_CROSSOVER_JSON.exists():
        pytest.skip("case_crossover_results.json not generated")
    monkeypatch.setattr(figures_module, "OUTPUT_DIR", tmp_path)
    out = figures_module.make_figure_s2()
    assert out is not None
    assert out.exists()
    assert out.stat().st_size > 1000  # non-empty PNG


def test_make_figure_s3_writes_png(figures_module, tmp_path, monkeypatch):
    if not figures_module.PREF_IRR_JSON.exists():
        pytest.skip("prefecture_irr_by_prefecture.json not generated")
    monkeypatch.setattr(figures_module, "OUTPUT_DIR", tmp_path)
    out = figures_module.make_figure_s3()
    assert out is not None
    assert out.exists()
    assert out.stat().st_size > 1000
