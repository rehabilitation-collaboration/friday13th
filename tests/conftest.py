"""Shared pytest fixtures for friday13th tests."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


def _load_src_module(filename: str, alias: str):
    """Load a src/*.py file whose name starts with a digit (invalid identifier).

    Cached in sys.modules under `alias` so repeated tests share the module.
    """
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, SRC_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def nb_module():
    """Load src/02_prefecture_panel_nb.py under an importable alias."""
    return _load_src_module("02_prefecture_panel_nb.py", "prefecture_panel_nb")


@pytest.fixture(scope="session")
def jma_weather_module():
    """Load src/06b_scrape_jma_weather.py under an importable alias."""
    return _load_src_module("06b_scrape_jma_weather.py", "jma_weather_scrape")


@pytest.fixture(scope="session")
def weather_nb_module():
    """Load src/03_prefecture_panel_weather_nb.py under an importable alias."""
    return _load_src_module(
        "03_prefecture_panel_weather_nb.py", "prefecture_panel_weather_nb"
    )


@pytest.fixture(scope="session")
def build_panels_module():
    """Load src/01a_build_panels.py under an importable alias
    (Phase 2C-C2-e P2-3: 01a had zero pytest coverage before this fixture)."""
    return _load_src_module("01a_build_panels.py", "build_panels")


@pytest.fixture(scope="session")
def diagnostics_module():
    """Load src/04_diagnostics.py under an importable alias
    (Phase 2C-C1: NB diagnostics + pair cluster bootstrap)."""
    return _load_src_module("04_diagnostics.py", "diagnostics")


@pytest.fixture(scope="session")
def diagnostics_json():
    """Return parsed output/diagnostics_results.json. Skip if the file is
    missing (Phase 2C-C1 has not been generated in this checkout)."""
    import json
    path = REPO_ROOT / "output" / "diagnostics_results.json"
    if not path.exists():
        pytest.skip(f"diagnostics_results.json missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def case_crossover_module():
    """Load src/05_case_crossover.py under an importable alias
    (Phase 2C-C3: 3 case-crossover alternative tests)."""
    return _load_src_module("05_case_crossover.py", "case_crossover")


@pytest.fixture(scope="session")
def case_crossover_json():
    """Return parsed output/case_crossover_results.json. Skip if the file is
    missing (Phase 2C-C3 has not been generated in this checkout)."""
    import json
    path = REPO_ROOT / "output" / "case_crossover_results.json"
    if not path.exists():
        pytest.skip(f"case_crossover_results.json missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def case_crossover_pairs(case_crossover_module):
    """Cached pairs dataframe reused across unit tests (avoids re-reading 1.88M-row parquet).

    Skips (not errors) when the fullmoon-accident parquet is missing, matching
    the diagnostics_json / accidents_pref_codes pattern (2C-C3 P3-l fix).
    """
    parquet_path = case_crossover_module.ACCIDENTS_PARQUET
    if not parquet_path.exists():
        pytest.skip(f"accidents_clean.parquet missing: {parquet_path}")
    daily = case_crossover_module.load_accidents_daily()
    return case_crossover_module.extract_case_control_pairs(daily)


@pytest.fixture(scope="session")
def pref_by_pref_module():
    """Load src/07_prefecture_by_prefecture_fit.py under an importable alias
    (Phase 2C-C4: per-prefecture NB fit for Figure S3 forest)."""
    return _load_src_module(
        "07_prefecture_by_prefecture_fit.py", "prefecture_by_prefecture_fit"
    )


@pytest.fixture(scope="session")
def pref_by_pref_json():
    """Return parsed output/prefecture_irr_by_prefecture.json. Skip if the
    file is missing (Phase 2C-C4 has not been generated in this checkout)."""
    import json
    path = REPO_ROOT / "output" / "prefecture_irr_by_prefecture.json"
    if not path.exists():
        pytest.skip(f"prefecture_irr_by_prefecture.json missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def merge_truth_module():
    """Load src/08_merge_truth.py under an importable alias
    (Phase 2C-C5: V1 base + Phase 2C JSON → truth.json)."""
    return _load_src_module("08_merge_truth.py", "merge_truth")


@pytest.fixture(scope="session")
def diagnostics_03_primary_ctx(diagnostics_module):
    """One NB2 fit for 03_primary shared across unit tests (P2-9 M17 fix).

    Avoids refitting per-test — the panel loader + NB2 fit costs ~5-8s.
    Returns dict with spec + design + fits so individual tests can
    directly invoke dispersion/pearson/quasi_poisson/hc1/spec_sensitivity/
    pair_cluster_bootstrap without paying the full run_all_diagnostics cost.
    """
    specs = diagnostics_module.build_specs()
    spec = next(s for s in specs if s["label"] == "03_primary")
    df = getattr(spec["module"], spec["loader_name"])()
    X, y = spec["module"].build_design(df, spec["fe_cols"])
    groups = spec["module"].build_cluster_groups(df)
    fits = diagnostics_module.fit_nb2_with_objects(y, X, groups, spec["label"])
    return {
        "spec": spec,
        "df": df,
        "X": X,
        "y": y,
        "groups": groups,
        "fits": fits,
    }

FULLMOON_ACCIDENTS = Path(
    "/Users/mizukishirai/claude/analysis/fullmoon-accident/data/processed/accidents_clean.parquet"
)
JMA_MASTER = Path(
    "/Users/mizukishirai/claude/analysis/fullmoon-accident/data/raw/jma/jma_cloud_cover_daily.parquet"
)


@pytest.fixture(scope="session")
def mapping_entries():
    import pref_mapping

    pref_mapping.load_mapping.cache_clear()
    return pref_mapping.load_mapping()


@pytest.fixture(scope="session")
def accidents_pref_codes():
    """51 unique pref_codes from the accident parquet."""
    if not FULLMOON_ACCIDENTS.exists():
        pytest.skip(f"Accident parquet missing: {FULLMOON_ACCIDENTS}")
    import pandas as pd

    df = pd.read_parquet(FULLMOON_ACCIDENTS, columns=["pref_code"])
    return set(int(c) for c in df["pref_code"].dropna().unique())


@pytest.fixture(scope="session")
def jma_master_stations():
    """station_id set from the merged JMA cloud master cache."""
    if not JMA_MASTER.exists():
        pytest.skip(f"JMA master cache missing: {JMA_MASTER}")
    import pandas as pd

    df = pd.read_parquet(JMA_MASTER, columns=["station_id"])
    return set(df["station_id"].unique())
