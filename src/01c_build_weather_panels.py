"""
Aggregate JMA daily precipitation, snowfall, and snow depth to two panel
levels matching the accident panels.

Aggregation rules (mirrors 01b_build_cloud_panels.py):
  - Prefecture-level panel = 47 prefectures x 2192 days
      * 46 prefectures: 1 station -> pass-through
      * Hokkaido: 5 stations -> SIMPLE MEAN of each weather variable.
        We reject fatality/population weighting for the same
        exposure-endogeneity reason spelled out in 01b: weighting weather
        by accident-heavy areas re-introduces the very bias GPT V1 Major 5
        flagged.
  - Bureau-level panel = 51 police bureaus x 2192 days
      * Each bureau -> its assigned representative station (1:1 lookup).

Inputs:
  friday13th/data/raw/jma_weather/precip_snow_daily.parquet  (51 stations,
    produced by 06b_scrape_jma_weather.py)
  friday13th/data/pref_station_map.json

Outputs:
  friday13th/data/processed/weather_by_prefecture_daily.parquet
  friday13th/data/processed/weather_by_bureau_daily.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

FRIDAY13 = Path(__file__).parent.parent
JMA_MASTER = FRIDAY13 / "data" / "raw" / "jma_weather" / "precip_snow_daily.parquet"
OUT_DIR = FRIDAY13 / "data" / "processed"

sys.path.insert(0, str(FRIDAY13 / "src"))
import pref_mapping  # noqa: E402

DATE_START = "2019-01-01"
DATE_END = "2024-12-31"

WEATHER_COLS = ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm")


def load_master() -> pd.DataFrame:
    df = pd.read_parquet(JMA_MASTER)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_bureau_weather(master: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, pref_code): 1:1 station lookup, no aggregation."""
    slim = mapping[["pref_code", "prefecture_en", "police_bureau_en",
                    "region", "jma_block_no"]]
    merged = slim.merge(master, left_on="jma_block_no", right_on="station_id", how="left")
    keep = ["date", "pref_code", "prefecture_en", "police_bureau_en",
            "region", "jma_block_no", *WEATHER_COLS]
    merged = merged[keep].sort_values(["date", "pref_code"]).reset_index(drop=True)
    return merged


def build_prefecture_weather(master: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (date, prefecture): simple mean across stations in that prefecture.
    46 prefectures = pass-through (1 station).
    Hokkaido = mean of 5 stations (Sapporo/Hakodate/Asahikawa/Kushiro/Abashiri).
    """
    station_to_pref = (
        mapping[["jma_block_no", "prefecture_en"]]
        .drop_duplicates()
        .set_index("jma_block_no")["prefecture_en"]
        .to_dict()
    )
    df = master.copy()
    df["prefecture_en"] = df["station_id"].map(station_to_pref)
    assert df["prefecture_en"].notna().all(), "station without prefecture mapping"

    agg_map = {col: (col, "mean") for col in WEATHER_COLS}
    agg_map["n_stations"] = ("station_id", "nunique")

    grouped = (
        df.groupby(["date", "prefecture_en"], sort=False)
        .agg(**agg_map)
        .reset_index()
    )
    region_map = mapping[["prefecture_en", "region"]].drop_duplicates()
    grouped = grouped.merge(region_map, on="prefecture_en", how="left")
    return grouped.sort_values(["date", "prefecture_en"]).reset_index(drop=True)


def sanity_check(bureau: pd.DataFrame, pref: pd.DataFrame) -> None:
    n_days = (pd.Timestamp(DATE_END) - pd.Timestamp(DATE_START)).days + 1
    assert n_days == 2192, n_days
    assert bureau.shape[0] == 51 * n_days, (bureau.shape, 51 * n_days)
    assert pref.shape[0] == 47 * n_days, (pref.shape, 47 * n_days)

    hok = pref[pref["prefecture_en"] == "Hokkaido"]
    assert (hok["n_stations"] == 5).all(), hok["n_stations"].value_counts()

    non_hok = pref[pref["prefecture_en"] != "Hokkaido"]
    assert (non_hok["n_stations"] == 1).all(), non_hok["n_stations"].value_counts()

    assert pref["prefecture_en"].nunique() == 47


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = pd.DataFrame(pref_mapping.load_mapping())

    print("Loading JMA weather master cache ...", flush=True)
    master = load_master()
    print(f"  loaded {len(master):,} rows / {master['station_id'].nunique()} stations",
          flush=True)

    print("Building bureau-level weather panel (1:1) ...", flush=True)
    bureau = build_bureau_weather(master, mapping)

    print("Building prefecture-level weather panel (simple mean; Hokkaido = 5-station mean) ...",
          flush=True)
    pref = build_prefecture_weather(master, mapping)

    sanity_check(bureau, pref)

    bureau_out = OUT_DIR / "weather_by_bureau_daily.parquet"
    pref_out = OUT_DIR / "weather_by_prefecture_daily.parquet"
    bureau.to_parquet(bureau_out, index=False)
    pref.to_parquet(pref_out, index=False)

    print(f"\nSaved: {bureau_out}  shape={bureau.shape}", flush=True)
    print(f"Saved: {pref_out}  shape={pref.shape}", flush=True)

    print("\n=== Prefecture weather stats ===")
    for col in WEATHER_COLS:
        s = pref[col]
        print(f"  {col}: mean={s.mean():.3f}, std={s.std():.3f}, null={s.isna().sum()}")

    print("\n=== Bureau weather stats ===")
    for col in WEATHER_COLS:
        s = bureau[col]
        print(f"  {col}: mean={s.mean():.3f}, std={s.std():.3f}, null={s.isna().sum()}")


if __name__ == "__main__":
    main()
