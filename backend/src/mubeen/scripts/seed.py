"""Seed Columbus-area masjids.

Idempotent — safe to re-run at any time.  A masjid is skipped when a row
with the same (name, address_line) already exists.

Usage:
    uv run seed-masjids
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from uuid import uuid4

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mubeen.config import settings
from mubeen.db.models.masjid import IqamahTime, JumuahTime, Masjid

log = structlog.get_logger()


# ── Seed data structures ──────────────────────────────────────────────────────

@dataclass
class _Iqamah:
    prayer: str
    fixed_time: time | None = None
    minutes_after_adhan: int | None = None


@dataclass
class _Jumuah:
    time: time
    label: str = "Jumuʿah"
    language: str = "en"
    sort_order: int = 0


@dataclass
class _Masjid:
    name: str
    address_line: str
    city: str
    state: str
    lat: float
    lon: float
    calculation_method: str = "ISNA"
    country: str = "US"
    phone: str | None = None
    website: str | None = None
    iqamah: list[_Iqamah] = field(default_factory=list)
    jumuah: list[_Jumuah] = field(default_factory=list)


# ── Columbus-area masjid data ────────────────────────────────────────────────
# Coordinates are precise to ~50 m.  Iqamah times are typical mid-year values;
# operators should update them seasonally once they claim their listing.

SEEDS: list[_Masjid] = [
    _Masjid(
        name="Daarul Ahbaab دار الأحباب",
        address_line="5079 Westerville Rd",
        city="Columbus",
        state="OH",
        lat=40.0816,
        lon=-82.9393,
        calculation_method="ISNA",
        iqamah=[
            _Iqamah("fajr",    fixed_time=time(5, 45)),
            _Iqamah("dhuhr",   fixed_time=time(13, 15)),
            _Iqamah("asr",     fixed_time=time(16, 45)),
            _Iqamah("maghrib", minutes_after_adhan=5),
            _Iqamah("isha",    fixed_time=time(21, 0)),
        ],
        jumuah=[
            _Jumuah(time=time(13, 30), label="Jumuʿah", language="en", sort_order=0),
        ],
    ),
    _Masjid(
        name="Noor Islamic Cultural Center",
        address_line="5001 Trabue Rd",
        city="Columbus",
        state="OH",
        lat=40.0019,
        lon=-83.1178,
        calculation_method="ISNA",
        website="https://www.noorusa.org",
        iqamah=[
            _Iqamah("fajr",    fixed_time=time(6, 0)),
            _Iqamah("dhuhr",   fixed_time=time(13, 30)),
            _Iqamah("asr",     fixed_time=time(17, 0)),
            _Iqamah("maghrib", minutes_after_adhan=5),
            _Iqamah("isha",    fixed_time=time(21, 15)),
        ],
        jumuah=[
            _Jumuah(time=time(13, 0),  label="First Jumuʿah",  language="en", sort_order=0),
            _Jumuah(time=time(14, 15), label="Second Jumuʿah", language="en", sort_order=1),
        ],
    ),
    _Masjid(
        name="Islamic Society of Greater Columbus",
        address_line="1428 E Broad St",
        city="Columbus",
        state="OH",
        lat=39.9638,
        lon=-82.9706,
        calculation_method="ISNA",
        iqamah=[
            _Iqamah("fajr",    fixed_time=time(5, 30)),
            _Iqamah("dhuhr",   fixed_time=time(13, 15)),
            _Iqamah("asr",     fixed_time=time(16, 30)),
            _Iqamah("maghrib", minutes_after_adhan=10),
            _Iqamah("isha",    fixed_time=time(20, 45)),
        ],
        jumuah=[
            _Jumuah(time=time(13, 30), label="Jumuʿah", language="en", sort_order=0),
        ],
    ),
    _Masjid(
        name="Ohio Islamic Cultural Center",
        address_line="2590 E Broad St",
        city="Columbus",
        state="OH",
        lat=39.9591,
        lon=-82.9480,
        calculation_method="ISNA",
        iqamah=[
            _Iqamah("fajr",    fixed_time=time(5, 45)),
            _Iqamah("dhuhr",   fixed_time=time(13, 0)),
            _Iqamah("asr",     fixed_time=time(16, 45)),
            _Iqamah("maghrib", minutes_after_adhan=5),
            _Iqamah("isha",    fixed_time=time(20, 30)),
        ],
        jumuah=[
            _Jumuah(time=time(13, 30), label="Jumuʿah", language="en", sort_order=0),
        ],
    ),
    _Masjid(
        name="Masjid Abu Bakr",
        address_line="3412 S High St",
        city="Columbus",
        state="OH",
        lat=39.9224,
        lon=-83.0064,
        calculation_method="ISNA",
        iqamah=[
            _Iqamah("fajr",    fixed_time=time(6, 0)),
            _Iqamah("dhuhr",   fixed_time=time(13, 15)),
            _Iqamah("asr",     fixed_time=time(16, 30)),
            _Iqamah("maghrib", minutes_after_adhan=5),
            _Iqamah("isha",    fixed_time=time(21, 0)),
        ],
        jumuah=[
            _Jumuah(time=time(13, 30), label="Jumuʿah", language="en", sort_order=0),
        ],
    ),
]


# ── Insert logic ──────────────────────────────────────────────────────────────

def _seed_one(session: Session, seed: _Masjid) -> bool:
    """Insert masjid + child rows.  Returns True if inserted, False if skipped."""
    existing = session.execute(
        select(Masjid).where(
            Masjid.name == seed.name,
            Masjid.address_line == seed.address_line,
        )
    ).scalar_one_or_none()

    if existing is not None:
        return False

    masjid = Masjid(
        id=uuid4(),
        name=seed.name,
        address_line=seed.address_line,
        city=seed.city,
        state=seed.state,
        country=seed.country,
        lat=seed.lat,
        lon=seed.lon,
        calculation_method=seed.calculation_method,
        phone=seed.phone,
        website=seed.website,
    )
    session.add(masjid)
    session.flush()  # materialise masjid.id before child inserts

    for iq in seed.iqamah:
        session.add(
            IqamahTime(
                id=uuid4(),
                masjid_id=masjid.id,
                prayer=iq.prayer,
                fixed_time=iq.fixed_time,
                minutes_after_adhan=iq.minutes_after_adhan,
            )
        )

    for jt in seed.jumuah:
        session.add(
            JumuahTime(
                id=uuid4(),
                masjid_id=masjid.id,
                label=jt.label,
                language=jt.language,
                time=jt.time,
                sort_order=jt.sort_order,
            )
        )

    return True


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    engine = create_engine(settings.database_url_sync, echo=False)
    inserted = skipped = 0

    with Session(engine) as session:
        for seed in SEEDS:
            if _seed_one(session, seed):
                inserted += 1
                log.info("seeded", masjid=seed.name)
            else:
                skipped += 1
                log.info("skipped", masjid=seed.name, reason="already exists")
        session.commit()

    engine.dispose()
    print(f"\n✓  {inserted} inserted, {skipped} skipped.\n")
