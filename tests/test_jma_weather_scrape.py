"""
Tests for src/06b_scrape_jma_weather.py.

Layout:
  - Light tests (this file top): parse_amount() sentinel handling.
    Runnable at any time; no external I/O.
  - Slow tests (marked @pytest.mark.slow): require per-station parquet
    caches under data/raw/jma_weather/. Skipped automatically until the
    Phase 2C-C2-d full scrape has run.

Sentinel convention (JMA daily_s1.php):
  "--"   -> 0.0   (phenomenon absent for the day, treated as zero)
  "×"    -> NaN   (missing observation)
  ""     -> NaN
  ")"    -> stripped from tail (資料不足値 marker)
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

FRIDAY13 = Path(__file__).parent.parent
WEATHER_RAW_DIR = FRIDAY13 / "data" / "raw" / "jma_weather"


# ---------- Light tests: parse_amount ----------

def test_parse_amount_double_dash_is_zero(jma_weather_module):
    """JMA '--' means the phenomenon did not occur; treat as 0.0."""
    assert jma_weather_module.parse_amount("--") == 0.0


def test_parse_amount_cross_is_nan(jma_weather_module):
    """JMA '×' means observation missing; treat as NaN."""
    assert math.isnan(jma_weather_module.parse_amount("×"))


def test_parse_amount_empty_is_nan(jma_weather_module):
    assert math.isnan(jma_weather_module.parse_amount(""))


def test_parse_amount_none_is_nan(jma_weather_module):
    assert math.isnan(jma_weather_module.parse_amount(None))


def test_parse_amount_plain_float(jma_weather_module):
    assert jma_weather_module.parse_amount("2.5") == 2.5


def test_parse_amount_zero_string(jma_weather_module):
    """A cell that literally reads '0.0' is a real observation of zero."""
    assert jma_weather_module.parse_amount("0.0") == 0.0


def test_parse_amount_trailing_paren_marker(jma_weather_module):
    """'0.5)' is a data-shortage-flagged 0.5; keep the number, drop the marker."""
    assert jma_weather_module.parse_amount("0.5)") == 0.5


def test_parse_amount_trailing_bracket_marker(jma_weather_module):
    """'1.2]' is a data-incomplete-flagged 1.2; keep the number."""
    assert jma_weather_module.parse_amount("1.2]") == 1.2


def test_parse_amount_dashdash_with_space_paren(jma_weather_module):
    """'-- )' still means phenomenon absent (0.0); the ')' is a quality tag.
    Observed in Sapporo late-October pilot rows."""
    assert jma_weather_module.parse_amount("-- )") == 0.0


def test_parse_amount_dashdash_with_space_bracket(jma_weather_module):
    """'-- ]' likewise = 0.0. Observed in Sapporo early-November pilot rows."""
    assert jma_weather_module.parse_amount("-- ]") == 0.0


def test_parse_amount_value_with_space_marker(jma_weather_module):
    """'0.5 )' (space before marker) also parses as 0.5."""
    assert jma_weather_module.parse_amount("0.5 )") == 0.5


def test_parse_amount_whitespace_tolerance(jma_weather_module):
    assert jma_weather_module.parse_amount("  3.4  ") == 3.4


def test_parse_amount_invalid_is_nan(jma_weather_module):
    assert math.isnan(jma_weather_module.parse_amount("abc"))


def test_parse_amount_int_string(jma_weather_module):
    """Snow depth cells like '5' (no decimal) parse as float."""
    assert jma_weather_module.parse_amount("5") == 5.0


# ---------- Slow tests: cache-dependent ----------

@pytest.mark.slow
def test_pilot_station_cache_exists():
    """After pilot run, data/raw/jma_weather/precip_snow_47412.parquet exists."""
    cache = WEATHER_RAW_DIR / "precip_snow_47412.parquet"
    if not cache.exists():
        pytest.skip(f"Pilot cache missing: {cache}")
    import pandas as pd

    df = pd.read_parquet(cache)
    assert len(df) >= 2100  # ~2192 days, allow small parser drops
    assert set(df.columns) >= {
        "station_id", "date", "precipitation_mm",
        "snowfall_cm", "snow_depth_max_cm",
    }
    # Sapporo must show non-trivial winter snowfall
    snow_positive = int((df["snowfall_cm"] > 0).sum())
    assert snow_positive >= 50, f"Sapporo snowfall>0 days = {snow_positive}, expected >=50"


@pytest.mark.slow
def test_master_cache_51_stations():
    """After full scrape, master cache has all 51 stations x ~2192 days."""
    cache = WEATHER_RAW_DIR / "precip_snow_daily.parquet"
    if not cache.exists():
        pytest.skip(f"Master cache missing: {cache}")
    import pandas as pd

    df = pd.read_parquet(cache)
    assert df["station_id"].nunique() == 51
    # 51 * 2192 = 111,792 target; parser may drop a handful of rows
    assert len(df) >= 51 * 2100


@pytest.mark.slow
def test_prefecture_weather_panel_shape():
    """Prefecture panel: 47 x 2192 rows, Hokkaido aggregated from 5 stations."""
    processed = FRIDAY13 / "data" / "processed" / "weather_by_prefecture_daily.parquet"
    if not processed.exists():
        pytest.skip(f"Prefecture panel missing: {processed}")
    import pandas as pd

    df = pd.read_parquet(processed)
    assert df.shape[0] == 47 * 2192, f"expected 47*2192, got {df.shape[0]}"
    assert df["prefecture_en"].nunique() == 47

    hok = df[df["prefecture_en"] == "Hokkaido"]
    assert (hok["n_stations"] == 5).all(), hok["n_stations"].value_counts()

    non_hok = df[df["prefecture_en"] != "Hokkaido"]
    assert (non_hok["n_stations"] == 1).all(), non_hok["n_stations"].value_counts()

    assert set(df.columns) >= {
        "date", "prefecture_en", "region",
        "precipitation_mm", "snowfall_cm", "snow_depth_max_cm", "n_stations",
    }


@pytest.mark.slow
def test_bureau_weather_panel_shape():
    """Bureau panel: 51 x 2192 rows, 1:1 station pass-through."""
    processed = FRIDAY13 / "data" / "processed" / "weather_by_bureau_daily.parquet"
    if not processed.exists():
        pytest.skip(f"Bureau panel missing: {processed}")
    import pandas as pd

    df = pd.read_parquet(processed)
    assert df.shape[0] == 51 * 2192, f"expected 51*2192, got {df.shape[0]}"
    assert df["pref_code"].nunique() == 51
    assert set(df.columns) >= {
        "date", "pref_code", "prefecture_en", "police_bureau_en",
        "region", "jma_block_no",
        "precipitation_mm", "snowfall_cm", "snow_depth_max_cm",
    }


@pytest.mark.slow
def test_weather_panels_no_all_null_stations():
    """No station may be entirely NaN for precipitation across all days."""
    processed = FRIDAY13 / "data" / "processed" / "weather_by_bureau_daily.parquet"
    if not processed.exists():
        pytest.skip(f"Bureau panel missing: {processed}")
    import pandas as pd

    df = pd.read_parquet(processed)
    per_station = df.groupby("jma_block_no")["precipitation_mm"].apply(
        lambda s: s.notna().sum()
    )
    dead = per_station[per_station < 2000]
    assert dead.empty, f"stations with <2000 non-null precip days: {dead.to_dict()}"
