"""TDD: calculation-method validation on PATCH and POST masjid endpoints.

Behaviour that does not yet exist
──────────────────────────────────
• PatchMasjidRequest.calculation_method is str | None with no validator, so any
  string (including garbage) reaches the database with a 200.
• RegisterMasjidRequest.calculation_method has the same gap.
• "UOIF" is absent from CALCULATION_METHOD_MAP; the service silently falls back
  to NORTH_AMERICA instead of raising.

Tests expected to fail now
──────────────────────────
  test_patch_invalid_calc_method_returns_422   — currently 200 (no validator)
  test_post_invalid_calc_method_returns_422    — currently 201 (no validator)
  test_uoif_accepted_and_produces_prayer_times — fails on first assertion
      ("UOIF" not in CALCULATION_METHOD_MAP)

Implementation required to green this suite
───────────────────────────────────────────
1. Add @field_validator("calculation_method") to PatchMasjidRequest that rejects
   values not in _VALID_METHODS.
2. Add the same validator to RegisterMasjidRequest.
3. Add "UOIF" to _VALID_METHODS in schemas/masjid.py.
4. Add "UOIF" → CalculationMethod.<constant> to CALCULATION_METHOD_MAP in
   services/prayer_times.py.
"""

from __future__ import annotations

from httpx import AsyncClient

from mubeen.db.models.masjid import Masjid
from mubeen.db.models.operator import OperatorAccount
from mubeen.services.prayer_times import CALCULATION_METHOD_MAP

_PASSWORD = "Str0ng-Passw0rd!"

_VALID_REGISTRATION_BODY: dict = {
    "name": "Masjid Test CalcMethod",
    "address_line": "1 Test St",
    "city": "Detroit",
    "state": "MI",
    "country": "US",
    "lat": 42.3314,
    "lon": -83.0458,
    "calculation_method": "ISNA",
    "timezone": "America/Detroit",
}


async def _signup_and_login(client: AsyncClient, *, email: str) -> str:
    """Sign up a fresh masjid-less operator and return their JWT."""
    await client.post("/api/auth/signup", json={"email": email, "password": _PASSWORD})
    resp = await client.post("/api/auth/login", json={"email": email, "password": _PASSWORD})
    assert resp.status_code == 200, f"login failed: {resp.text}"
    return resp.json()["access_token"]


# ── PATCH /api/masjids/{id} ───────────────────────────────────────────────────


async def test_patch_isna_returns_200(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    """ISNA is a valid method; PATCH must accept it and return 200.

    This test guards the baseline so that adding a validator does not
    accidentally break a currently-valid method.
    """
    _, token = seed_operator
    resp = await client.patch(
        f"/api/masjids/{seed_masjid.id}",
        json={"calculation_method": "ISNA"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


async def test_patch_invalid_calc_method_returns_422(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    """An unrecognised method string must be rejected with 422 before reaching the DB."""
    _, token = seed_operator
    resp = await client.patch(
        f"/api/masjids/{seed_masjid.id}",
        json={"calculation_method": "NONSENSE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ── POST /api/masjids ─────────────────────────────────────────────────────────


async def test_post_invalid_calc_method_returns_422(client: AsyncClient) -> None:
    """Registering a masjid with an invalid method string must return 422.

    Uses a fresh operator (no existing masjid role) so the calc-method
    validation — not a 409 role-conflict — is the reason for rejection.
    """
    tok = await _signup_and_login(client, email="calc-invalid@test.mubeen")
    resp = await client.post(
        "/api/masjids",
        json={**_VALID_REGISTRATION_BODY, "calculation_method": "NONSENSE"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 422


# ── UOIF: accepted and produces prayer times ──────────────────────────────────


async def test_uoif_accepted_and_produces_prayer_times(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    """UOIF must be a first-class method: PATCH accepts it (200), and the masjid
    detail endpoint returns all five prayer times computed via UOIF — not via a
    silent NORTH_AMERICA fallback.

    The guard assertion on CALCULATION_METHOD_MAP fails immediately in the current
    codebase and drives the implementation task.
    """
    assert "UOIF" in CALCULATION_METHOD_MAP, (
        "Add 'UOIF' → CalculationMethod.<constant> to CALCULATION_METHOD_MAP "
        "in services/prayer_times.py"
    )

    _, token = seed_operator
    patch_resp = await client.patch(
        f"/api/masjids/{seed_masjid.id}",
        json={"calculation_method": "UOIF"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_resp.status_code == 200

    detail_resp = await client.get(f"/api/masjids/{seed_masjid.id}")
    assert detail_resp.status_code == 200

    data = detail_resp.json()
    assert data["calculation_method"] == "UOIF"

    adhan = data["adhan_times"]
    for prayer in ("fajr", "dhuhr", "asr", "maghrib", "isha"):
        assert prayer in adhan, f"adhan_times missing key: {prayer!r}"
        assert adhan[prayer] is not None, f"adhan_times[{prayer!r}] is null"
