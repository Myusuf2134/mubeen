#!/usr/bin/env python3
"""
Pilot seed — 3 real masjids with iqamah times, jumu'ah times, and one operator account.

All inserts use ON CONFLICT … DO NOTHING with hardcoded UUIDs, so the script is
safe to run repeatedly without creating duplicates or touching rows an operator
has since edited.

Usage (from backend/):
    DATABASE_URL=postgresql+asyncpg://mubeen:mubeen@localhost:5432/mubeen \\
    uv run python scripts/seed_pilot.py

The operator account created here is for the pilot only:
    username : pilot-operator
    password : ChangeMe2025!
    scope    : Islamic Center of America (Dearborn, MI)
"""

from __future__ import annotations

import asyncio
import datetime
import os
from uuid import UUID

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://mubeen:mubeen@localhost:5432/mubeen",
)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()

# ── Hardcoded UUIDs — "5eed" prefix makes seed rows easy to identify ──────────
# Masjids
M_ICA = UUID("5eed0001-0000-4000-a000-000000000000")  # Islamic Center of America
M_DAR = UUID("5eed0002-0000-4000-a000-000000000000")  # Dar Al-Hijrah
M_FAR = UUID("5eed0003-0000-4000-a000-000000000000")  # Al-Farooq Atlanta

# Iqamah times  (5 per masjid, grouped in blocks of 5)
IQ = {
    "ica_fajr":    UUID("5eed1001-0000-4000-a000-000000000000"),
    "ica_dhuhr":   UUID("5eed1002-0000-4000-a000-000000000000"),
    "ica_asr":     UUID("5eed1003-0000-4000-a000-000000000000"),
    "ica_maghrib": UUID("5eed1004-0000-4000-a000-000000000000"),
    "ica_isha":    UUID("5eed1005-0000-4000-a000-000000000000"),
    "dar_fajr":    UUID("5eed1006-0000-4000-a000-000000000000"),
    "dar_dhuhr":   UUID("5eed1007-0000-4000-a000-000000000000"),
    "dar_asr":     UUID("5eed1008-0000-4000-a000-000000000000"),
    "dar_maghrib": UUID("5eed1009-0000-4000-a000-000000000000"),
    "dar_isha":    UUID("5eed100a-0000-4000-a000-000000000000"),
    "far_fajr":    UUID("5eed100b-0000-4000-a000-000000000000"),
    "far_dhuhr":   UUID("5eed100c-0000-4000-a000-000000000000"),
    "far_asr":     UUID("5eed100d-0000-4000-a000-000000000000"),
    "far_maghrib": UUID("5eed100e-0000-4000-a000-000000000000"),
    "far_isha":    UUID("5eed100f-0000-4000-a000-000000000000"),
}

# Jumu'ah times
JU = {
    "ica_1": UUID("5eed2001-0000-4000-a000-000000000000"),
    "ica_2": UUID("5eed2002-0000-4000-a000-000000000000"),
    "dar_1": UUID("5eed2003-0000-4000-a000-000000000000"),
    "far_1": UUID("5eed2004-0000-4000-a000-000000000000"),
    "far_2": UUID("5eed2005-0000-4000-a000-000000000000"),
}

# Operator
OP_ID = UUID("5eed0010-0000-4000-a000-000000000000")

# ── Seed data ─────────────────────────────────────────────────────────────────

MASJIDS = [
    {
        "id": M_ICA,
        "name": "Islamic Center of America",
        "address_line": "19500 Ford Rd",
        "city": "Dearborn",
        "state": "MI",
        "country": "US",
        "lat": 42.3219,
        "lon": -83.2065,
        "calculation_method": "ISNA",
        "phone": "(313) 593-0000",
        "website": "https://icofa.com",
    },
    {
        "id": M_DAR,
        "name": "Dar Al-Hijrah Islamic Center",
        "address_line": "3159 Row St",
        "city": "Falls Church",
        "state": "VA",
        "country": "US",
        "lat": 38.8537,
        "lon": -77.1596,
        "calculation_method": "ISNA",
        "phone": "(703) 536-6665",
        "website": "https://daralhijrah.net",
    },
    {
        "id": M_FAR,
        "name": "Al-Farooq Masjid of Atlanta",
        "address_line": "442 14th St NW",
        "city": "Atlanta",
        "state": "GA",
        "country": "US",
        "lat": 33.7831,
        "lon": -84.3934,
        "calculation_method": "ISNA",
        "phone": "(404) 874-7521",
        "website": None,
    },
]

def _t(h: int, m: int) -> datetime.time:
    return datetime.time(h, m, 0)


# (uuid_key, masjid_id, prayer, minutes_after_adhan, fixed_time | None)
IQAMAH_ROWS = [
    # ICA — fixed Fajr, offsets for the rest
    ("ica_fajr",    M_ICA, "fajr",    None, _t(6, 0)),
    ("ica_dhuhr",   M_ICA, "dhuhr",   20,   None),
    ("ica_asr",     M_ICA, "asr",     15,   None),
    ("ica_maghrib", M_ICA, "maghrib", 5,    None),
    ("ica_isha",    M_ICA, "isha",    15,   None),
    # Dar Al-Hijrah — offset-based throughout
    ("dar_fajr",    M_DAR, "fajr",    20,   None),
    ("dar_dhuhr",   M_DAR, "dhuhr",   20,   None),
    ("dar_asr",     M_DAR, "asr",     15,   None),
    ("dar_maghrib", M_DAR, "maghrib", 5,    None),
    ("dar_isha",    M_DAR, "isha",    15,   None),
    # Al-Farooq — fixed Fajr, offsets for the rest
    ("far_fajr",    M_FAR, "fajr",    None, _t(5, 45)),
    ("far_dhuhr",   M_FAR, "dhuhr",   15,   None),
    ("far_asr",     M_FAR, "asr",     15,   None),
    ("far_maghrib", M_FAR, "maghrib", 5,    None),
    ("far_isha",    M_FAR, "isha",    15,   None),
]

# (uuid_key, masjid_id, label, language, time, sort_order)
JUMUAH_ROWS = [
    ("ica_1", M_ICA, "1st Jumu'ah",     "en", _t(13,  0), 0),
    ("ica_2", M_ICA, "2nd Jumu'ah",     "en", _t(14, 30), 1),
    ("dar_1", M_DAR, "Jumu'ah",         "en", _t(13, 15), 0),
    ("far_1", M_FAR, "1st Khutbah",     "en", _t(13,  0), 0),
    ("far_2", M_FAR, "الخطبة الثانية", "ar", _t(14, 15), 1),
]

OPERATOR = {
    "id": OP_ID,
    "masjid_id": M_ICA,
    "username": "pilot-operator",
    "password": "ChangeMe2025!",
}

# ── SQL ───────────────────────────────────────────────────────────────────────

_INSERT_MASJID = text("""
    INSERT INTO masjids
        (id, name, address_line, city, state, country,
         lat, lon, calculation_method, phone, website)
    VALUES
        (:id, :name, :address_line, :city, :state, :country,
         :lat, :lon, :calculation_method, :phone, :website)
    ON CONFLICT (id) DO NOTHING
""")

_INSERT_IQAMAH = text("""
    INSERT INTO iqamah_times
        (id, masjid_id, prayer, minutes_after_adhan, fixed_time)
    VALUES
        (:id, :masjid_id, :prayer, :minutes_after_adhan, :fixed_time)
    ON CONFLICT ON CONSTRAINT uq_iqamah_masjid_prayer DO NOTHING
""")

_INSERT_JUMUAH = text("""
    INSERT INTO jumuah_times
        (id, masjid_id, label, language, time, sort_order)
    VALUES
        (:id, :masjid_id, :label, :language, :time, :sort_order)
    ON CONFLICT (id) DO NOTHING
""")

_INSERT_OPERATOR = text("""
    INSERT INTO operator_accounts
        (id, masjid_id, username, hashed_password)
    VALUES
        (:id, :masjid_id, :username, :hashed_password)
    ON CONFLICT ON CONSTRAINT uq_operator_username DO NOTHING
""")

# ── Runner ────────────────────────────────────────────────────────────────────

async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)

    inserted: dict[str, int] = {
        "masjids": 0,
        "iqamah_times": 0,
        "jumuah_times": 0,
        "operator_accounts": 0,
    }
    skipped: dict[str, int] = dict(inserted)

    async with engine.begin() as conn:
        # Masjids
        for row in MASJIDS:
            r = await conn.execute(_INSERT_MASJID, row)
            if r.rowcount:
                inserted["masjids"] += 1
            else:
                skipped["masjids"] += 1

        # Iqamah times
        for key, masjid_id, prayer, minutes, fixed in IQAMAH_ROWS:
            r = await conn.execute(_INSERT_IQAMAH, {
                "id": IQ[key],
                "masjid_id": masjid_id,
                "prayer": prayer,
                "minutes_after_adhan": minutes,
                "fixed_time": fixed,
            })
            if r.rowcount:
                inserted["iqamah_times"] += 1
            else:
                skipped["iqamah_times"] += 1

        # Jumu'ah times
        for key, masjid_id, label, lang, time_str, sort_order in JUMUAH_ROWS:
            r = await conn.execute(_INSERT_JUMUAH, {
                "id": JU[key],
                "masjid_id": masjid_id,
                "label": label,
                "language": lang,
                "time": time_str,
                "sort_order": sort_order,
            })
            if r.rowcount:
                inserted["jumuah_times"] += 1
            else:
                skipped["jumuah_times"] += 1

        # Operator account (hash generated fresh but only inserted once)
        r = await conn.execute(_INSERT_OPERATOR, {
            "id": OPERATOR["id"],
            "masjid_id": OPERATOR["masjid_id"],
            "username": OPERATOR["username"],
            "hashed_password": _hash_password(OPERATOR["password"]),
        })
        if r.rowcount:
            inserted["operator_accounts"] += 1
        else:
            skipped["operator_accounts"] += 1

    await engine.dispose()

    print("\nPilot seed summary")
    print("──────────────────────────────")
    for table in inserted:
        i, s = inserted[table], skipped[table]
        print(f"  {table:<22}  {i} inserted  {s} already existed")

    if inserted["operator_accounts"]:
        print(f"\n  Operator created:")
        print(f"    username : {OPERATOR['username']}")
        print(f"    password : {OPERATOR['password']}")
        print(f"    scope    : Islamic Center of America ({M_ICA})")
        print(f"\n  ⚠  Change the password before any real use.")
    else:
        print(f"\n  Operator '{OPERATOR['username']}' already exists — password unchanged.")

    print()


if __name__ == "__main__":
    asyncio.run(main())
