"""Operator authentication tests — signup, login, and /api/admin/me.

Written BEFORE implementation (Phase 4).  Every test here is expected to
fail until the following endpoints are built:

  POST /api/auth/signup   — register an operator for a masjid
  POST /api/auth/login    — verify credentials, return a JWT
  GET  /api/admin/me      — return the calling operator's profile

Design assumptions (to be honoured by the implementation):
  - Signup accepts:  {"email": str, "password": str, "masjid_id": uuid}
  - Login accepts:   {"email": str, "password": str}
  - Login returns:   {"access_token": str, "token_type": "bearer"}
  - /admin/me returns at minimum: {"email": str}
  - Passwords are hashed with bcrypt; raw/hashed forms never appear in responses
  - Minimum password length is 12 characters (enforced by Pydantic schema → 422)
  - Duplicate email returns 409 Conflict
  - Wrong password and unknown email return identical 401 detail strings
    (prevents user-enumeration)
  - /admin/me with no token → 401; tampered/expired token → 401
"""

from __future__ import annotations

import datetime

import jwt
import pytest
from httpx import AsyncClient

from mubeen.config import settings
from mubeen.db.models.masjid import Masjid

# ── Constants ─────────────────────────────────────────────────────────────────

_EMAIL = "imam@masjid-al-noor.com"
_PASSWORD = "Str0ng-Passw0rd!"        # 16 chars — passes ≥12 rule
_SHORT_PASSWORD = "tooshort"           # 8 chars — must return 422
_WRONG_PASSWORD = "WrongPassword-99!"  # valid format but incorrect


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _signup(
    client: AsyncClient,
    masjid: Masjid,
    *,
    email: str = _EMAIL,
    password: str = _PASSWORD,
) -> object:
    return await client.post(
        "/api/auth/signup",
        json={"email": email, "password": password, "masjid_id": str(masjid.id)},
    )


async def _login(
    client: AsyncClient,
    *,
    email: str = _EMAIL,
    password: str = _PASSWORD,
) -> object:
    return await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )


# ── Signup ────────────────────────────────────────────────────────────────────


async def test_signup_new_email_returns_201(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    resp = await _signup(client, seed_masjid)
    assert resp.status_code == 201


async def test_signup_response_contains_no_password_fields(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    resp = await _signup(client, seed_masjid)
    assert resp.status_code == 201
    body = resp.json()
    assert "password" not in body
    assert "hashed_password" not in body


async def test_signup_duplicate_email_returns_409(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)
    resp = await _signup(client, seed_masjid)  # same email, same masjid
    assert resp.status_code == 409


async def test_signup_short_password_returns_422(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    resp = await _signup(client, seed_masjid, password=_SHORT_PASSWORD)
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────


async def test_login_correct_credentials_returns_200(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)
    resp = await _login(client)
    assert resp.status_code == 200


async def test_login_correct_credentials_returns_nonempty_access_token(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)
    resp = await _login(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("access_token"), "access_token must be present and non-empty"


async def test_login_wrong_password_returns_401(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)
    resp = await _login(client, password=_WRONG_PASSWORD)
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    resp = await _login(client, email="nobody@example.com")
    assert resp.status_code == 401


async def test_login_wrong_password_and_unknown_email_return_identical_detail(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    """Wrong password and unknown email must return the same 401 detail string.

    Different messages would let an attacker enumerate registered emails.
    """
    await _signup(client, seed_masjid)
    wrong_pw = await _login(client, password=_WRONG_PASSWORD)
    unknown_email = await _login(client, email="nobody@example.com")
    assert wrong_pw.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_pw.json()["detail"] == unknown_email.json()["detail"]


# ── GET /api/admin/me ─────────────────────────────────────────────────────────


async def test_me_no_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/admin/me")
    assert resp.status_code == 401


async def test_me_valid_token_returns_200(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)
    login_resp = await _login(client)
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/api/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


async def test_me_valid_token_returns_correct_email(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)
    login_resp = await _login(client)
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/api/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == _EMAIL


async def test_me_tampered_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/admin/me",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.tampered.payload"},
    )
    assert resp.status_code == 401


async def test_me_expired_token_returns_401(
    client: AsyncClient,
    seed_masjid: Masjid,
) -> None:
    await _signup(client, seed_masjid)

    expired_token = jwt.encode(
        {
            "sub": _EMAIL,
            "exp": datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    resp = await client.get(
        "/api/admin/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401
