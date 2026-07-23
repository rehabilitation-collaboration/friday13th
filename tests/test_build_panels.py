"""Contract tests for src/01a_build_panels.py (Phase 2C-C2-e P2-3 fix).

01a's runtime `sanity_check()` is a strong belt-and-suspenders guard when
someone manually runs `python src/01a_build_panels.py`, but it never fires
under `pytest tests/`. These tests exercise the holiday CSV loader and the
calendar-covariate derivation directly so a regression is caught in CI, not
only on next parquet regeneration.

Also asserts the is_holiday × is_newyear overlap of 7 dates (Jan 1 × 6yr +
2023-01-02 substitute holiday) that 01a::sanity_check does not explicitly
check (P3-7 companion fix).
"""
from __future__ import annotations

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# load_holidays
# ---------------------------------------------------------------------------
def test_load_holidays_returns_111_dates(build_panels_module):
    holidays = build_panels_module.load_holidays()
    assert len(holidays) == 111


def test_load_holidays_returns_naive_timestamps_in_range(build_panels_module):
    """Timestamps must be tz-naive and within 2019-2024 (the panel window)."""
    holidays = build_panels_module.load_holidays()
    for d in holidays:
        assert isinstance(d, pd.Timestamp), d
        assert d.tz is None, d
        assert 2019 <= d.year <= 2024, d


def test_load_holidays_covers_all_six_years(build_panels_module):
    """Each of 2019-2024 has at least 15 recognised national holidays."""
    holidays = build_panels_module.load_holidays()
    years = pd.Series([d.year for d in holidays]).value_counts().sort_index()
    for year in range(2019, 2025):
        assert year in years.index, year
        assert years[year] >= 15, (year, years[year])


# ---------------------------------------------------------------------------
# add_calendar_covariates
# ---------------------------------------------------------------------------
def test_calendar_covariates_populates_all_flags(build_panels_module):
    """Spot-check three semantically distinct dates."""
    df = pd.DataFrame(
        {"date": pd.to_datetime(["2021-01-01", "2021-08-13", "2020-05-05"])}
    )
    holidays = build_panels_module.load_holidays()
    out = build_panels_module.add_calendar_covariates(df.copy(), holidays)

    # 2021-01-01 元日: national holiday AND New Year period
    assert out.loc[0, "is_holiday"] == 1
    assert out.loc[0, "is_newyear"] == 1
    assert out.loc[0, "is_obon"] == 0
    assert out.loc[0, "is_fri13"] == 0

    # 2021-08-13 Fri13 AND Obon initial day; NOT a national holiday
    assert out.loc[1, "is_fri13"] == 1
    assert out.loc[1, "is_obon"] == 1
    assert out.loc[1, "is_holiday"] == 0

    # 2020-05-05 こどもの日: national holiday, neither obon nor newyear
    assert out.loc[2, "is_holiday"] == 1
    assert out.loc[2, "is_obon"] == 0
    assert out.loc[2, "is_newyear"] == 0


def test_obon_flag_matches_hardcoded_8_13_to_16(build_panels_module):
    """Full-window sweep: is_obon fires exactly on 8/13-16 each year."""
    df = pd.DataFrame({"date": pd.date_range("2019-01-01", "2024-12-31")})
    holidays = build_panels_module.load_holidays()
    out = build_panels_module.add_calendar_covariates(df, holidays)
    obon = out[out["is_obon"] == 1]
    assert obon["month"].eq(8).all()
    assert obon["day_of_month"].between(13, 16).all()
    assert obon.shape[0] == 6 * 4  # 6 years x 4 days


def test_newyear_flag_matches_hardcoded_1_1_to_3(build_panels_module):
    df = pd.DataFrame({"date": pd.date_range("2019-01-01", "2024-12-31")})
    holidays = build_panels_module.load_holidays()
    out = build_panels_module.add_calendar_covariates(df, holidays)
    ny = out[out["is_newyear"] == 1]
    assert ny["month"].eq(1).all()
    assert ny["day_of_month"].between(1, 3).all()
    assert ny.shape[0] == 6 * 3  # 6 years x 3 days


# ---------------------------------------------------------------------------
# Cross-flag structure
# ---------------------------------------------------------------------------
def test_holiday_and_newyear_overlap_exactly_seven_dates(build_panels_module):
    """P3-7 companion: is_holiday × is_newyear = 7 dates (元日 6件
    + 2023-01-02 substitute holiday because 元日 fell on Sunday).
    This is an intended overlap (元日 is BOTH a national holiday AND
    within the New Year period), not a bug — but neither 01a::sanity_check
    nor the pre-fix test suite asserted it, so a future off-by-one in
    holidays parsing could go undetected."""
    df = pd.DataFrame({"date": pd.date_range("2019-01-01", "2024-12-31")})
    holidays = build_panels_module.load_holidays()
    out = build_panels_module.add_calendar_covariates(df, holidays)
    overlap = out[(out["is_holiday"] == 1) & (out["is_newyear"] == 1)]
    assert overlap.shape[0] == 7, (
        f"Expected 7 dates (元日 6 years + 2023-01-02 substitute), "
        f"got {overlap.shape[0]}: {overlap['date'].dt.strftime('%Y-%m-%d').tolist()}"
    )


def test_fri13_and_holiday_disjoint(build_panels_module):
    """Handoff-critical: none of the 10 Fri13 dates in 2019-2024 is a national
    holiday, so is_holiday cleanly captures a distinct confounder (not a
    fri13-collinear noise term)."""
    df = pd.DataFrame({"date": pd.date_range("2019-01-01", "2024-12-31")})
    holidays = build_panels_module.load_holidays()
    out = build_panels_module.add_calendar_covariates(df, holidays)
    both = out[(out["is_fri13"] == 1) & (out["is_holiday"] == 1)]
    assert both.empty, (
        f"Fri13 × holiday overlap unexpectedly non-empty: "
        f"{both['date'].dt.strftime('%Y-%m-%d').tolist()}"
    )


def test_fri13_and_obon_intersect_only_on_2021_08_13(build_panels_module):
    """The single Obon-Fri13 collision that motivates is_obon's inclusion."""
    df = pd.DataFrame({"date": pd.date_range("2019-01-01", "2024-12-31")})
    holidays = build_panels_module.load_holidays()
    out = build_panels_module.add_calendar_covariates(df, holidays)
    both = out[(out["is_fri13"] == 1) & (out["is_obon"] == 1)]
    assert both.shape[0] == 1
    assert both["date"].dt.strftime("%Y-%m-%d").iloc[0] == "2021-08-13"
