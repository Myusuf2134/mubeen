"""Unit tests that pin the prayer_times service contract.

The critical invariant: tzfpy.get_tz takes (lng, lat) — longitude first.
If that order were accidentally swapped, Minneapolis (-93.27, 44.98) would
resolve to a wrong timezone and prayer times would silently shift by hours.
These tests catch that regression without needing the database.
"""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import pytest

from mubeen.services.prayer_times import CALCULATION_METHOD_MAP, get_adhan_times

# Minneapolis downtown — unambiguously America/Chicago
_LAT = 44.98
_LON = -93.27


def test_timezone_resolves_to_america_chicago() -> None:
    result = get_adhan_times(_LAT, _LON, "ISNA")
    for prayer, dt in result.items():
        assert dt.tzinfo == ZoneInfo("America/Chicago"), (
            f"{prayer}: expected America/Chicago, got {dt.tzinfo!r} — "
            "check tzfpy.get_tz(lng, lat) argument order"
        )


def test_returns_five_named_prayers() -> None:
    result = get_adhan_times(_LAT, _LON, "ISNA")
    assert set(result.keys()) == {"fajr", "dhuhr", "asr", "maghrib", "isha"}


def test_prayer_times_are_tz_aware() -> None:
    result = get_adhan_times(_LAT, _LON, "ISNA")
    for prayer, dt in result.items():
        assert dt.tzinfo is not None, f"{prayer} is not tz-aware"


def test_prayer_ordering_fajr_before_isha() -> None:
    result = get_adhan_times(_LAT, _LON, "ISNA")
    order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    for earlier, later in zip(order, order[1:]):
        assert result[earlier] < result[later], (
            f"{earlier} should be before {later}"
        )


def test_for_date_parameter_is_respected() -> None:
    target = datetime.date(2025, 1, 15)
    result = get_adhan_times(_LAT, _LON, "ISNA", for_date=target)
    for dt in result.values():
        assert dt.date() == target


@pytest.mark.parametrize("method", list(CALCULATION_METHOD_MAP.keys()))
def test_all_calculation_methods_return_valid_times(method: str) -> None:
    result = get_adhan_times(_LAT, _LON, method)
    assert len(result) == 5
    for dt in result.values():
        assert dt.tzinfo is not None
