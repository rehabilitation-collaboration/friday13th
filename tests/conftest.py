"""Shared pytest fixtures for friday13th tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

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
