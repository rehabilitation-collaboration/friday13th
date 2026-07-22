"""
Tests for the NPA pref_code <-> prefecture <-> JMA station mapping.

Purpose: guarantee that the 51 police bureau codes discovered in the accident
parquet (2019-2024) are all wired to a real JMA station that we actually have
cloud data for. Regression guard for the '01-47' assumption that turned out to
be wrong at the start of Phase 2C.
"""
from __future__ import annotations

import re

import pytest

import pref_mapping


def test_mapping_has_51_entries(mapping_entries):
    assert len(mapping_entries) == 51


def test_mapping_covers_all_47_prefectures(mapping_entries):
    prefectures = {e["prefecture_en"] for e in mapping_entries}
    assert len(prefectures) == 47


def test_pref_codes_are_unique(mapping_entries):
    codes = [e["pref_code"] for e in mapping_entries]
    assert len(codes) == len(set(codes))


def test_police_bureaus_are_unique(mapping_entries):
    bureaus = [e["police_bureau_en"] for e in mapping_entries]
    assert len(bureaus) == len(set(bureaus)) == 51


def test_hokkaido_bureaus_split_into_5(mapping_entries):
    hokkaido = [e for e in mapping_entries if e["prefecture_en"] == "Hokkaido"]
    assert {e["pref_code"] for e in hokkaido} == {10, 11, 12, 13, 14}
    stations = {e["jma_station_en"] for e in hokkaido}
    assert stations == {"Sapporo", "Hakodate", "Asahikawa", "Kushiro", "Abashiri"}


def test_hokkaido_bureau_helper_matches_data(mapping_entries):
    for entry in mapping_entries:
        expected = entry["prefecture_en"] == "Hokkaido"
        assert pref_mapping.is_hokkaido_bureau(entry["pref_code"]) is expected


def test_jma_block_no_format(mapping_entries):
    for e in mapping_entries:
        assert re.fullmatch(r"47\d{3}", e["jma_block_no"]), e


def test_no_null_station_assignment(mapping_entries):
    for e in mapping_entries:
        assert e["jma_station_en"], e
        assert e["jma_block_no"], e
        assert isinstance(e["jma_prec_no"], int) and e["jma_prec_no"] > 0, e


def test_region_field_covered(mapping_entries):
    expected_regions = {
        "Hokkaido", "Tohoku", "Kanto", "Chubu",
        "Kinki", "Chugoku", "Shikoku", "Kyushu", "Okinawa",
    }
    regions = {e["region"] for e in mapping_entries}
    assert regions <= expected_regions
    # All 9 regions must be represented (Okinawa is 1 code alone)
    assert regions == expected_regions


def test_get_entry_and_helpers(mapping_entries):
    # Tokyo (30)
    assert pref_mapping.pref_code_to_prefecture(30) == "Tokyo"
    assert pref_mapping.pref_code_to_station(30) == "47662"
    # Osaka (62)
    assert pref_mapping.pref_code_to_prefecture(62) == "Osaka"
    assert pref_mapping.pref_code_to_station(62) == "47772"
    # Hokkaido Sapporo bureau (10)
    assert pref_mapping.pref_code_to_prefecture(10) == "Hokkaido"
    assert pref_mapping.pref_code_to_station(10) == "47412"
    # Gifu (53) - added in Phase 2C
    assert pref_mapping.pref_code_to_prefecture(53) == "Gifu"
    assert pref_mapping.pref_code_to_station(53) == "47632"


def test_get_entry_raises_on_unknown_code():
    with pytest.raises(KeyError):
        pref_mapping.get_entry(999)


@pytest.mark.slow
def test_mapping_matches_accident_data(mapping_entries, accidents_pref_codes):
    """Every pref_code appearing in NPA accident data must exist in mapping."""
    map_codes = {e["pref_code"] for e in mapping_entries}
    unmapped = accidents_pref_codes - map_codes
    unused = map_codes - accidents_pref_codes
    assert not unmapped, f"pref_codes in data but not in mapping: {sorted(unmapped)}"
    assert not unused, f"pref_codes in mapping but not in data: {sorted(unused)}"


@pytest.mark.slow
def test_every_station_has_jma_cloud_data(mapping_entries, jma_master_stations):
    """Every JMA station referenced by the mapping must have scraped cloud data."""
    map_stations = {e["jma_block_no"] for e in mapping_entries}
    missing = map_stations - jma_master_stations
    assert not missing, f"stations in mapping without JMA data: {sorted(missing)}"


@pytest.mark.slow
def test_gifu_station_present(jma_master_stations):
    """Gifu (47632) was added in Phase 2C-1a. Guard against accidental removal."""
    assert "47632" in jma_master_stations


def test_all_prefectures_helper():
    prefs = pref_mapping.all_prefectures()
    assert len(prefs) == 47
    assert prefs == sorted(prefs)


def test_all_pref_codes_helper():
    codes = pref_mapping.all_pref_codes()
    assert len(codes) == 51
    assert codes == sorted(codes)
    assert codes[0] == 10 and codes[-1] == 97
