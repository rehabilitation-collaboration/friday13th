"""
NPA pref_code (police bureau) <-> prefecture <-> JMA weather station mapping.

Data source: friday13th/data/pref_station_map.json
Built from:
  - NPA official code table (2_koudohyou_todouhukenkoudo.csv, 51 codes)
  - JMA STATIONS list (fullmoon-accident/src/06_scrape_jma_cloud.py, 51 stations
    after adding Gifu 47632 in Phase 2C)

Design:
  Hokkaido has 5 police bureaus (codes 10-14) split by regional command boundaries.
  We keep them as 5 separate 'police_bureau' units for the primary panel model
  (51-unit fixed-effects panel). A 'prefecture' field lets us collapse to
  47 prefectures for sensitivity analysis.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "pref_station_map.json"

REQUIRED_FIELDS = (
    "pref_code",
    "name_jp",
    "prefecture_en",
    "police_bureau_en",
    "region",
    "jma_block_no",
    "jma_prec_no",
    "jma_station_en",
)

HOKKAIDO_BUREAU_CODES = frozenset({10, 11, 12, 13, 14})


@lru_cache(maxsize=1)
def load_mapping() -> list[dict]:
    """Load and cache the pref_code -> station mapping."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Mapping file not found: {DATA_PATH}")
    entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for entry in entries:
        missing = [f for f in REQUIRED_FIELDS if f not in entry]
        if missing:
            raise ValueError(f"Entry missing fields {missing}: {entry}")
    return entries


@lru_cache(maxsize=1)
def _by_code() -> dict[int, dict]:
    return {e["pref_code"]: e for e in load_mapping()}


def get_entry(pref_code: int) -> dict:
    """Return full mapping entry for a police bureau code."""
    table = _by_code()
    if pref_code not in table:
        raise KeyError(f"Unknown pref_code: {pref_code}")
    return table[pref_code]


def pref_code_to_prefecture(pref_code: int) -> str:
    """Return the prefecture EN name (Hokkaido bureaus all map to 'Hokkaido')."""
    return get_entry(pref_code)["prefecture_en"]


def pref_code_to_station(pref_code: int) -> str:
    """Return the JMA block_no (5-digit string, e.g. '47662') for a police bureau."""
    return get_entry(pref_code)["jma_block_no"]


def all_pref_codes() -> list[int]:
    """Return the 51 police bureau codes in ascending order."""
    return sorted(_by_code().keys())


def all_prefectures() -> list[str]:
    """Return the 47 prefecture EN names."""
    return sorted({e["prefecture_en"] for e in load_mapping()})


def is_hokkaido_bureau(pref_code: int) -> bool:
    return pref_code in HOKKAIDO_BUREAU_CODES
