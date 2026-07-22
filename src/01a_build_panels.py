"""
Build long-panel daily accident data at two levels of aggregation:

  1. accidents_by_bureau_daily.parquet     -- 51 police bureau x 2192 days
  2. accidents_by_prefecture_daily.parquet -- 47 prefecture x 2192 days

Both panels carry the same day-level covariates (Fri13 flag, weekday, holiday,
year/month/day-of-month) plus per-unit counts (total / fatal / injury /
day-vs-night). Missing (date, unit) cells are filled with 0 counts so the
panel is a strict rectangle (no implicit-zero bias).

Input:  fullmoon-accident/data/processed/accidents_clean.parquet
Output: friday13th/data/processed/accidents_by_{bureau,prefecture}_daily.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

FRIDAY13 = Path(__file__).parent.parent
FULLMOON_ACC = Path(
    "/Users/mizukishirai/claude/analysis/fullmoon-accident/data/processed/accidents_clean.parquet"
)
OUT_DIR = FRIDAY13 / "data" / "processed"

sys.path.insert(0, str(FRIDAY13 / "src"))
import pref_mapping  # noqa: E402

DATE_START = "2019-01-01"
DATE_END = "2024-12-31"


def load_accidents() -> pd.DataFrame:
    cols = [
        "occurred_at", "pref_code", "accident_severity",
        "fatality_count", "injury_count", "daynight_code",
    ]
    df = pd.read_parquet(FULLMOON_ACC, columns=cols)
    df["date"] = df["occurred_at"].dt.normalize()
    df["is_fatal"] = (df["accident_severity"] == 1).astype(np.int32)
    df["is_night"] = df["daynight_code"].isin([21, 22, 23]).astype(np.int32)
    df["is_day"] = df["daynight_code"].isin([11, 12, 13]).astype(np.int32)
    return df


def build_bureau_panel(acc: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, pref_code); zero-fill missing."""
    grouped = (
        acc.groupby(["date", "pref_code"], sort=False)
        .agg(
            total_count=("pref_code", "size"),
            fatal_count=("is_fatal", "sum"),
            injury_count=("injury_count", "sum"),
            fatality_count=("fatality_count", "sum"),
            day_count=("is_day", "sum"),
            night_count=("is_night", "sum"),
        )
        .reset_index()
    )

    all_dates = pd.date_range(DATE_START, DATE_END, freq="D")
    all_codes = pref_mapping.all_pref_codes()
    scaffold = pd.MultiIndex.from_product(
        [all_dates, all_codes], names=["date", "pref_code"]
    ).to_frame(index=False)

    panel = scaffold.merge(grouped, on=["date", "pref_code"], how="left")
    count_cols = ["total_count", "fatal_count", "injury_count",
                  "fatality_count", "day_count", "night_count"]
    panel[count_cols] = panel[count_cols].fillna(0).astype(np.int32)

    slim = mapping[["pref_code", "prefecture_en", "police_bureau_en", "region"]]
    panel = panel.merge(slim, on="pref_code", how="left")
    assert panel["prefecture_en"].notna().all(), "unmapped pref_code in scaffold"
    return panel


def build_prefecture_panel(bureau_panel: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Collapse Hokkaido 5 bureaus into a single Hokkaido row per date."""
    count_cols = ["total_count", "fatal_count", "injury_count",
                  "fatality_count", "day_count", "night_count"]
    pref_panel = (
        bureau_panel.groupby(["date", "prefecture_en"], sort=False)[count_cols]
        .sum()
        .reset_index()
    )
    region_map = mapping[["prefecture_en", "region"]].drop_duplicates()
    pref_panel = pref_panel.merge(region_map, on="prefecture_en", how="left")
    return pref_panel


def add_calendar_covariates(panel: pd.DataFrame) -> pd.DataFrame:
    """Fri13 flag, weekday (Mon=0..Sun=6), year/month/day."""
    d = panel["date"]
    panel["year"] = d.dt.year.astype(np.int16)
    panel["month"] = d.dt.month.astype(np.int8)
    panel["day_of_month"] = d.dt.day.astype(np.int8)
    panel["weekday"] = d.dt.weekday.astype(np.int8)          # Mon=0..Sun=6
    panel["is_friday"] = (panel["weekday"] == 4).astype(np.int8)
    panel["is_13th"] = (panel["day_of_month"] == 13).astype(np.int8)
    panel["is_fri13"] = (panel["is_friday"] & panel["is_13th"]).astype(np.int8)
    return panel


def sanity_check(bureau: pd.DataFrame, pref: pd.DataFrame) -> None:
    n_days = (pd.Timestamp(DATE_END) - pd.Timestamp(DATE_START)).days + 1
    assert n_days == 2192, n_days
    assert bureau.shape[0] == 51 * n_days, (bureau.shape, 51 * n_days)
    assert pref.shape[0] == 47 * n_days, (pref.shape, 47 * n_days)

    # 10 Fri13 in 2019-2024
    fri13_dates = bureau.loc[bureau["is_fri13"] == 1, "date"].unique()
    assert len(fri13_dates) == 10, sorted(fri13_dates)

    # Totals must match parquet count
    total = bureau["total_count"].sum()
    assert total == 1_884_793, total

    pref_total = pref["total_count"].sum()
    assert pref_total == 1_884_793, pref_total

    # Fatal totals must match
    fatals = bureau["fatal_count"].sum()
    assert fatals == 16_257, fatals


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = pd.DataFrame(pref_mapping.load_mapping())

    print("Loading accidents ...", flush=True)
    acc = load_accidents()
    print(f"  loaded {len(acc):,} rows", flush=True)

    print("Building bureau panel ...", flush=True)
    bureau = add_calendar_covariates(build_bureau_panel(acc, mapping))

    print("Building prefecture panel ...", flush=True)
    pref = add_calendar_covariates(build_prefecture_panel(bureau, mapping))

    sanity_check(bureau, pref)

    bureau_out = OUT_DIR / "accidents_by_bureau_daily.parquet"
    pref_out = OUT_DIR / "accidents_by_prefecture_daily.parquet"
    bureau.to_parquet(bureau_out, index=False)
    pref.to_parquet(pref_out, index=False)

    print(f"\nSaved: {bureau_out}  shape={bureau.shape}", flush=True)
    print(f"Saved: {pref_out}  shape={pref.shape}", flush=True)

    # Preview: Fri13 daily totals (aggregated over units)
    fri13 = bureau.loc[bureau["is_fri13"] == 1].groupby("date")["total_count"].sum()
    print("\n=== Daily accident totals on the 10 Friday the 13th days ===")
    for date, cnt in fri13.items():
        print(f"  {date.date()}  total={cnt}")

    # Top-15 prefectures by 6-yr total
    top = (
        pref.groupby("prefecture_en")["total_count"].sum()
        .sort_values(ascending=False)
        .head(15)
    )
    print("\n=== 6-year totals by prefecture (top 15) ===")
    for name, v in top.items():
        print(f"  {name:<12s} {v:>10,}")


if __name__ == "__main__":
    main()
