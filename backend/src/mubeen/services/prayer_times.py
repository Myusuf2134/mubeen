"""Prayer time calculation using adhanpy (port of batoulapps/adhan-java).

Adhan (call-to-prayer) times are computed fresh from (lat, lon, calculation_method)
every request — never stored, because they change daily and are fully deterministic.
"""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import tzfpy
from adhanpy.calculation.CalculationMethod import CalculationMethod
from adhanpy.PrayerTimes import PrayerTimes

CALCULATION_METHOD_MAP: dict[str, CalculationMethod] = {
    "ISNA": CalculationMethod.NORTH_AMERICA,
    "MWL": CalculationMethod.MUSLIM_WORLD_LEAGUE,
    "UMM_AL_QURA": CalculationMethod.UMM_AL_QURA,
    "EGYPT": CalculationMethod.EGYPTIAN,
    "KARACHI": CalculationMethod.KARACHI,
    "DUBAI": CalculationMethod.DUBAI,
    "KUWAIT": CalculationMethod.KUWAIT,
    "QATAR": CalculationMethod.QATAR,
    "SINGAPORE": CalculationMethod.SINGAPORE,
    "MOON_SIGHTING_COMMITTEE": CalculationMethod.MOON_SIGHTING_COMMITTEE,
}


def get_adhan_times(
    lat: float,
    lon: float,
    calculation_method: str,
    for_date: datetime.date | None = None,
) -> dict[str, datetime.datetime]:
    """Return today's (or for_date's) adhan times as tz-aware datetimes in the masjid's local timezone."""
    tz_name = tzfpy.get_tz(lon, lat) or "UTC"  # tzfpy takes (lng, lat) order
    tz = ZoneInfo(tz_name)

    target_date = for_date or datetime.date.today()
    dt = datetime.datetime(target_date.year, target_date.month, target_date.day, tzinfo=tz)

    method = CALCULATION_METHOD_MAP.get(calculation_method, CalculationMethod.NORTH_AMERICA)
    pt = PrayerTimes((lat, lon), dt, calculation_method=method, time_zone=tz)

    return {
        "fajr": pt.fajr,
        "dhuhr": pt.dhuhr,
        "asr": pt.asr,
        "maghrib": pt.maghrib,
        "isha": pt.isha,
    }
