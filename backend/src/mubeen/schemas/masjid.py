from __future__ import annotations

import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# ── Response models ────────────────────────────────────────────────────────────


class MasjidSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    state: str
    country: str
    lat: float
    lon: float
    distance_km: float | None = None


class AdhanTimes(BaseModel):
    fajr: datetime.datetime
    dhuhr: datetime.datetime
    asr: datetime.datetime
    maghrib: datetime.datetime
    isha: datetime.datetime


class IqamahTimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prayer: str
    minutes_after_adhan: int | None
    fixed_time: datetime.time | None


class JumuahTimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str | None
    language: str | None
    time: datetime.time
    sort_order: int


class MasjidDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address_line: str
    city: str
    state: str
    country: str
    lat: float
    lon: float
    phone: str | None
    website: str | None
    calculation_method: str
    adhan_times: AdhanTimes
    iqamah_times: list[IqamahTimeOut]
    jumuah_times: list[JumuahTimeOut]
    has_live_session: bool
    latest_session_id: UUID | None


# ── Request models (extra="forbid" rejects unknown fields per spec §9) ─────────

_VALID_PRAYERS = {"fajr", "dhuhr", "asr", "maghrib", "isha"}
_VALID_METHODS = {"ISNA", "MWL", "UMM_AL_QURA", "EGYPT", "KARACHI", "DUBAI", "KUWAIT", "QATAR", "SINGAPORE", "MOON_SIGHTING_COMMITTEE"}


class IqamahTimeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prayer: Literal["fajr", "dhuhr", "asr", "maghrib", "isha"]
    minutes_after_adhan: int | None = None
    fixed_time: datetime.time | None = None

    @model_validator(mode="after")
    def one_must_be_set(self) -> IqamahTimeIn:
        if self.minutes_after_adhan is None and self.fixed_time is None:
            raise ValueError("set either minutes_after_adhan or fixed_time")
        if self.minutes_after_adhan is not None and self.minutes_after_adhan < 0:
            raise ValueError("minutes_after_adhan must be non-negative")
        return self


class PatchIqamahRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iqamah_times: list[IqamahTimeIn]

    @field_validator("iqamah_times")
    @classmethod
    def no_duplicate_prayers(cls, v: list[IqamahTimeIn]) -> list[IqamahTimeIn]:
        prayers = [entry.prayer for entry in v]
        if len(prayers) != len(set(prayers)):
            raise ValueError("duplicate prayer names in iqamah_times")
        return v


class JumuahTimeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    language: str | None = None
    time: datetime.time
    sort_order: int = 0

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 10:
            raise ValueError("language tag too long")
        return v


class PatchJumuahRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jumuah_times: list[JumuahTimeIn]
