"""
06b_scrape_jma_weather.py
Scrape JMA daily precipitation (mm) and snowfall (cm) from daily_s1.php.

Purpose (Phase 2C-C2-d):
  Extend the existing cloud_cover scraper with per-day precipitation,
  snowfall, and snow depth. Feeds the C2-e weather-adjusted panel NB
  regression so that GPT V1 Major 5 (weather endogeneity) is addressed
  with covariates beyond cloud cover alone.

Design:
  - Reuses the daily_s1.php URL and pagination scheme from
    fullmoon-accident/src/06_scrape_jma_cloud.py (same URL, one page per
    station per month, 21 <td> cells per data row after the two header rows).
  - Extracts by column position (verified via HTML inspection of
    Tokyo 47662 and Sapporo 47412 for 2020-01):
      cells[3]  -> precipitation_mm    (降水量 合計)
      cells[17] -> snowfall_cm         (雪 降雪 合計)
      cells[18] -> snow_depth_max_cm   (雪 最深積雪)
  - Sentinel handling (JMA convention):
      "--"           -> 0.0   (現象なし / phenomenon absent, treated as zero)
      ""             -> NaN   (empty cell)
      "×"            -> NaN   (欠測 / missing observation)
      trailing ")"   -> stripped (資料不足値 / data-shortage marker;
                                 numeric value retained)
  - Station list = pref_mapping.load_mapping() (51 stations, includes Gifu
    47632 and the Chiba/Yamaguchi replacements Choshi/Shimonoseki committed
    in the Phase 2C base).
  - fullmoon-accident is intentionally NOT touched. This scraper lives
    entirely in the friday13th tree so the fullmoon master cache stays
    pref_mapping-compliant and unrelated analyses aren't disturbed.

Output layout:
  data/raw/jma_weather/precip_snow_47XXX.parquet   (per-station cache)
  data/raw/jma_weather/precip_snow_daily.parquet   (master; written only
                                                    when the full station
                                                    set has been scraped)

Cost:
  51 stations x 72 months x 0.5s delay ≈ 30-40 minutes.
  Per-station cache makes the run interruption-tolerant.

Pilot mode (--pilot-block-no 47412):
  Scrape a single station (Sapporo by default; guaranteed snowfall in winter)
  and early-fail if any year has fewer than PILOT_MIN_NON_NULL_PER_YEAR
  non-null precipitation rows. Motivated by the Chiba/Yamaguchi failure mode
  found in Phase 2C base: a station can return HTTP 200 but empty payload.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

FRIDAY13 = Path(__file__).parent.parent
RAW_DIR = FRIDAY13 / "data" / "raw" / "jma_weather"
CACHE_FILE = RAW_DIR / "precip_snow_daily.parquet"

sys.path.insert(0, str(FRIDAY13 / "src"))
import pref_mapping  # noqa: E402

YEARS = range(2019, 2025)
REQUEST_DELAY = 0.5
MAX_RETRIES = 3
PILOT_MIN_NON_NULL_PER_YEAR = 200  # of ~365; abort early if a year underperforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_amount(cell: str | None) -> float:
    """
    Parse a JMA daily amount cell (precipitation mm, snowfall cm, or snow depth cm).

    Sentinel handling (JMA daily_s1.php convention, per 気象庁 statistics legend):
      None or ""      -> NaN
      "--"            -> 0.0   (現象なし / phenomenon absent for the day)
      "×"             -> NaN   (欠測 / missing observation)
      "0.5)"          -> 0.5   ")" = 資料不足値 (data-shortage) — value retained
      "-- )" / "-- ]" -> 0.0   quality markers can trail the "--" sentinel with
                               a separating space; the phenomenon-absent
                               interpretation still applies (observed in the
                               Sapporo pilot around initial-snowfall boundaries
                               in late October / early November).
      "1.2 ]"         -> 1.2   "]" = 資料不完全 (data-incomplete) — value retained
      numeric-like    -> float(value)
      anything else   -> NaN
    """
    if cell is None:
        return float("nan")
    s = cell.strip()
    if s == "":
        return float("nan")
    # Peel any number of trailing quality markers (")" data-shortage,
    # "]" data-incomplete) together with the whitespace that may precede them.
    while s and s[-1] in ")]":
        s = s[:-1].rstrip()
    if s == "":
        return float("nan")
    if s == "--":
        return 0.0
    if s == "×":
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def scrape_month(session: requests.Session, block_no: str, prec_no: int,
                 year: int, month: int) -> list[dict]:
    """
    Scrape one month of daily precipitation + snowfall from JMA daily_s1.php.
    Returns list of dicts.
    """
    url = "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php"
    params = {
        "prec_no": str(prec_no),
        "block_no": block_no,
        "year": str(year),
        "month": str(month),
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, params=params, timeout=60)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                break
        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return []
    else:
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    main_table = None
    for t in soup.find_all("table"):
        if len(t.find_all("tr")) > 30:
            main_table = t
            break

    if main_table is None:
        return []

    records: list[dict] = []
    for tr in main_table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < 20:
            continue
        try:
            day = int(cells[0])
        except (ValueError, IndexError):
            continue

        precip_mm = parse_amount(cells[3]) if len(cells) > 3 else float("nan")
        snow_cm = parse_amount(cells[17]) if len(cells) > 17 else float("nan")
        snow_depth_cm = parse_amount(cells[18]) if len(cells) > 18 else float("nan")

        records.append({
            "station_id": block_no,
            "date": f"{year}-{month:02d}-{day:02d}",
            "precipitation_mm": precip_mm,
            "snowfall_cm": snow_cm,
            "snow_depth_max_cm": snow_depth_cm,
        })

    return records


def _pilot_early_fail_check(records: list[dict], block_no: str, year: int) -> None:
    """Abort if a year's non-null precipitation count is below threshold."""
    if not records:
        raise RuntimeError(f"Pilot: station {block_no} year {year} returned zero rows")
    df = pd.DataFrame(records)
    non_null = int(df["precipitation_mm"].notna().sum())
    if non_null < PILOT_MIN_NON_NULL_PER_YEAR:
        raise RuntimeError(
            f"Pilot: station {block_no} year {year} has only {non_null} "
            f"non-null precipitation rows (< {PILOT_MIN_NON_NULL_PER_YEAR})"
        )


def scrape_all(max_stations: int | None = None,
               pilot_block_no: str | None = None) -> pd.DataFrame:
    """
    Scrape all (or a subset of) stations across YEARS.

    max_stations   : limit number of stations scraped (from pref_mapping order).
    pilot_block_no : if set, scrape only this block_no with per-year
                     early-fail QA (overrides max_stations).
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    mapping = pref_mapping.load_mapping()
    stations_full = [(e["jma_block_no"], e["jma_prec_no"], e["jma_station_en"])
                     for e in mapping]

    # dedup on block_no while preserving order (Hokkaido has 5 bureaus but
    # each has a distinct block_no; guard against future duplicates anyway)
    seen: set[str] = set()
    stations_unique: list[tuple[str, int, str]] = []
    for row in stations_full:
        if row[0] in seen:
            continue
        seen.add(row[0])
        stations_unique.append(row)

    full_station_count = len(stations_unique)

    pilot_mode = pilot_block_no is not None
    if pilot_mode:
        stations = [s for s in stations_unique if s[0] == pilot_block_no]
        if not stations:
            raise ValueError(f"pilot_block_no {pilot_block_no} not in mapping")
    elif max_stations is not None:
        stations = stations_unique[:max_stations]
    else:
        stations = stations_unique

    # Master cache shortcut only in full-run mode
    if CACHE_FILE.exists() and not pilot_mode and max_stations is None:
        logger.info("Master cache exists: %s", CACHE_FILE)
        return pd.read_parquet(CACHE_FILE)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (research)"})

    all_records: list[dict] = []
    total_months = len(stations) * len(YEARS) * 12
    done = 0

    for s_idx, (block_no, prec_no, name) in enumerate(stations):
        station_cache = RAW_DIR / f"precip_snow_{block_no}.parquet"
        if station_cache.exists() and not pilot_mode:
            logger.info("[%d/%d] %s (%s): cached", s_idx + 1, len(stations), name, block_no)
            df_cached = pd.read_parquet(station_cache)
            all_records.extend(df_cached.to_dict("records"))
            done += len(YEARS) * 12
            continue

        logger.info("[%d/%d] %s (%s) ...", s_idx + 1, len(stations), name, block_no)
        station_records: list[dict] = []

        for year in YEARS:
            year_records: list[dict] = []
            for month in range(1, 13):
                records = scrape_month(session, block_no, prec_no, year, month)
                year_records.extend(records)
                station_records.extend(records)
                done += 1
                time.sleep(REQUEST_DELAY)

            if done % 60 == 0:
                logger.info("  Progress: %d/%d months (%.0f%%)",
                            done, total_months, 100 * done / total_months)

            if pilot_mode:
                _pilot_early_fail_check(year_records, block_no, year)

        if station_records:
            df_station = pd.DataFrame(station_records)
            df_station["date"] = pd.to_datetime(df_station["date"])
            df_station.to_parquet(station_cache, index=False)
            all_records.extend(station_records)
            logger.info("  %s: %d rows saved -> %s", name, len(station_records), station_cache)

    if not all_records:
        logger.warning("No data scraped")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df["date"] = pd.to_datetime(df["date"])

    # Only refresh the master cache when the full station set was scraped.
    scraped_full_set = (not pilot_mode) and (max_stations is None
                                             or max_stations >= full_station_count)
    if scraped_full_set:
        df.to_parquet(CACHE_FILE, index=False)
        logger.info("Master cache saved: %s (%d records)", CACHE_FILE, len(df))
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-stations", type=int, default=None,
                        help="Limit number of stations scraped (from pref_mapping order).")
    parser.add_argument("--pilot-block-no", type=str, default=None,
                        help="Scrape only this block_no with per-year early-fail QA.")
    args = parser.parse_args()

    df = scrape_all(max_stations=args.max_stations, pilot_block_no=args.pilot_block_no)
    if df.empty:
        return

    logger.info("=== Summary ===")
    logger.info("rows=%d, stations=%d, dates=%s - %s",
                len(df), df["station_id"].nunique(),
                df["date"].min().date(), df["date"].max().date())
    for col in ("precipitation_mm", "snowfall_cm", "snow_depth_max_cm"):
        s = df[col]
        logger.info("  %s: mean=%.3f std=%.3f min=%.2f max=%.2f null=%d zero=%d",
                    col, float(np.nanmean(s)), float(np.nanstd(s)),
                    float(np.nanmin(s)) if s.notna().any() else float("nan"),
                    float(np.nanmax(s)) if s.notna().any() else float("nan"),
                    int(s.isna().sum()), int((s == 0.0).sum()))


if __name__ == "__main__":
    main()
