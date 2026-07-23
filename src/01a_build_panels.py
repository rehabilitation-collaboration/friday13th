"""
Build long-panel daily accident data at two levels of aggregation:

  1. accidents_by_bureau_daily.parquet     -- 51 police bureau x 2192 days
  2. accidents_by_prefecture_daily.parquet -- 47 prefecture x 2192 days

Both panels carry the same day-level covariates (Fri13 flag, weekday, holiday,
year/month/day-of-month) plus per-unit counts (total / fatal / injury /
day-vs-night). Missing (date, unit) cells are filled with 0 counts so the
panel is a strict rectangle (no implicit-zero bias).

Confounder flags added in Phase 2C-C2-e:
  - is_holiday:  Japanese national holidays sourced from Cabinet Office CSV
                 (data/jp_holidays_2019_2024.csv, 111 dates 2019-2024).
  - is_obon:     Hardcoded 8/13-16 each year (Obon travel period; not a
                 national holiday but a major domestic travel event that
                 confounds Fri13 traffic exposure -- notably 2021-08-13 which
                 is both Fri13 and Obon initial day).
  - is_newyear:  Hardcoded 1/1-3 each year.

Input:  fullmoon-accident/data/processed/accidents_clean.parquet
        friday13th/data/jp_holidays_2019_2024.csv
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
HOLIDAYS_CSV = FRIDAY13 / "data" / "jp_holidays_2019_2024.csv"

sys.path.insert(0, str(FRIDAY13 / "src"))
import pref_mapping  # noqa: E402

DATE_START = "2019-01-01"
DATE_END = "2024-12-31"


def load_holidays() -> set:
    """Return set of Japanese national holiday dates from Cabinet Office CSV.

    Source: https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv
    Original encoding is Shift-JIS; CSV in-repo is converted to UTF-8.
    """
    if not HOLIDAYS_CSV.exists():
        raise FileNotFoundError(
            f"Holiday CSV not found: {HOLIDAYS_CSV}.\n"
            "Regenerate from https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv:\n"
            "  curl -sS -o /tmp/s.csv <url> && \\\n"
            "  iconv -f SHIFT-JIS -t UTF-8 /tmp/s.csv | \\\n"
            "  awk -F, 'NR>1 && $1 ~ /^(2019|2020|2021|2022|2023|2024)/ {\n"
            "    gsub(/\\//, \"-\", $1); printf \"%s,%s\\n\", $1, $2}' \\\n"
            "  > data/jp_holidays_2019_2024.csv"
        )
    df = pd.read_csv(HOLIDAYS_CSV, parse_dates=["date"])
    return set(df["date"])


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


def add_calendar_covariates(panel: pd.DataFrame, holidays: set) -> pd.DataFrame:
    """Fri13, weekday, national-holiday / obon / newyear flags, year/month/day."""
    d = panel["date"]
    panel["year"] = d.dt.year.astype(np.int16)
    panel["month"] = d.dt.month.astype(np.int8)
    panel["day_of_month"] = d.dt.day.astype(np.int8)
    panel["weekday"] = d.dt.weekday.astype(np.int8)          # Mon=0..Sun=6
    panel["is_friday"] = (panel["weekday"] == 4).astype(np.int8)
    panel["is_13th"] = (panel["day_of_month"] == 13).astype(np.int8)
    panel["is_fri13"] = (panel["is_friday"] & panel["is_13th"]).astype(np.int8)
    panel["is_holiday"] = d.isin(holidays).astype(np.int8)
    panel["is_obon"] = (
        (panel["month"] == 8) & panel["day_of_month"].between(13, 16)
    ).astype(np.int8)
    panel["is_newyear"] = (
        (panel["month"] == 1) & panel["day_of_month"].between(1, 3)
    ).astype(np.int8)
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

    # Phase 2C-C2-e flags
    # is_holiday: 111 national-holiday dates x 51 bureau / x 47 pref
    holiday_dates_bureau = bureau.loc[bureau["is_holiday"] == 1, "date"].nunique()
    holiday_dates_pref = pref.loc[pref["is_holiday"] == 1, "date"].nunique()
    assert holiday_dates_bureau == 111, holiday_dates_bureau
    assert holiday_dates_pref == 111, holiday_dates_pref
    assert (bureau["is_holiday"] == 1).sum() == 111 * 51
    assert (pref["is_holiday"] == 1).sum() == 111 * 47

    # is_obon: 6 years x 4 days (8/13-16) = 24 dates
    obon_dates = bureau.loc[bureau["is_obon"] == 1, "date"].nunique()
    assert obon_dates == 24, obon_dates
    assert (bureau["is_obon"] == 1).sum() == 24 * 51
    assert (pref["is_obon"] == 1).sum() == 24 * 47

    # is_newyear: 6 years x 3 days (1/1-3) = 18 dates
    newyear_dates = bureau.loc[bureau["is_newyear"] == 1, "date"].nunique()
    assert newyear_dates == 18, newyear_dates
    assert (bureau["is_newyear"] == 1).sum() == 18 * 51
    assert (pref["is_newyear"] == 1).sum() == 18 * 47

    # 2021-08-13 must be both is_fri13=1 and is_obon=1 (the key confounding case)
    obon_fri13_rows = bureau[
        (bureau["is_obon"] == 1) & (bureau["is_fri13"] == 1)
    ]
    assert obon_fri13_rows.shape[0] == 51, obon_fri13_rows.shape
    assert (
        obon_fri13_rows["date"].dt.strftime("%Y-%m-%d").eq("2021-08-13")
    ).all(), obon_fri13_rows["date"].unique()

    # Sanity: national-holiday and obon are disjoint from Fri13 EXCEPT via is_obon
    # (i.e. no Fri13 date is a national holiday, per CAO data)
    fri13_and_holiday = bureau[
        (bureau["is_fri13"] == 1) & (bureau["is_holiday"] == 1)
    ]
    assert fri13_and_holiday.empty, fri13_and_holiday["date"].unique()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = pd.DataFrame(pref_mapping.load_mapping())

    print("Loading holidays ...", flush=True)
    holidays = load_holidays()
    print(f"  loaded {len(holidays):,} national-holiday dates", flush=True)

    print("Loading accidents ...", flush=True)
    acc = load_accidents()
    print(f"  loaded {len(acc):,} rows", flush=True)

    print("Building bureau panel ...", flush=True)
    bureau = add_calendar_covariates(build_bureau_panel(acc, mapping), holidays)

    print("Building prefecture panel ...", flush=True)
    pref = add_calendar_covariates(build_prefecture_panel(bureau, mapping), holidays)

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
        is_obon = (date.month == 8 and 13 <= date.day <= 16)
        tag = "  [Obon]" if is_obon else ""
        print(f"  {date.date()}  total={cnt}{tag}")

    # Top-15 prefectures by 6-yr total
    top = (
        pref.groupby("prefecture_en")["total_count"].sum()
        .sort_values(ascending=False)
        .head(15)
    )
    print("\n=== 6-year totals by prefecture (top 15) ===")
    for name, v in top.items():
        print(f"  {name:<12s} {v:>10,}")

    # Phase 2C-C2-e: confounder-flag summary
    print("\n=== Phase 2C-C2-e confounder flags (bureau panel) ===")
    print(f"  is_holiday : {(bureau['is_holiday']==1).sum():>7,} rows  "
          f"({bureau.loc[bureau['is_holiday']==1, 'date'].nunique()} unique dates)")
    print(f"  is_obon    : {(bureau['is_obon']==1).sum():>7,} rows  "
          f"({bureau.loc[bureau['is_obon']==1, 'date'].nunique()} unique dates)")
    print(f"  is_newyear : {(bureau['is_newyear']==1).sum():>7,} rows  "
          f"({bureau.loc[bureau['is_newyear']==1, 'date'].nunique()} unique dates)")


if __name__ == "__main__":
    main()
