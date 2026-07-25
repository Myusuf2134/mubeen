"""Tests for masjid registration, ownership, soft-deletes, and audit logging.

Written BEFORE implementation (TDD).  All tests are expected to fail until
the following are built:

  Endpoints
  ─────────
  POST   /api/masjids               — register a new masjid; calling operator becomes owner
  DELETE /api/masjids/{id}          — soft-delete (archive); sets deleted_at
  POST   /api/masjids/{id}/restore  — restore; clears deleted_at
  PATCH  /api/masjids/{id}          — update masjid metadata

  New models
  ──────────
  mubeen.db.models.masjid.MasjidOperatorRole
      id, masjid_id, operator_id, role ('owner' | …), created_at

  mubeen.db.models.audit.MasjidAuditLog
      id, masjid_id, operator_id, action, old_values (JSON), new_values (JSON), created_at

  Schema changes
  ──────────────
  Masjid  ← adds  deleted_at (DateTime nullable), timezone (String nullable)

  conftest note
  ─────────────
  Once the migrations exist, add 'masjid_operator_roles' and 'masjid_audit_logs'
  to _CLEANUP_TABLES in conftest.py (before 'operator_accounts').
"""

from __future__ import annotations

from uuid import UUID

import jwt
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.config import settings
from mubeen.db.models.masjid import Masjid
from mubeen.db.models.operator import OperatorAccount

# ── Shared constants ──────────────────────────────────────────────────────────

_OP_A = "op-a@test.mubeen"
_OP_B = "op-b@test.mubeen"
_PASSWORD = "Str0ng-Passw0rd!"

# Default valid registration payload.  Individual tests override specific keys.
_MASJID_BODY: dict = {
    "name": "Masjid Al-Huda",
    "address_line": "789 Olentangy River Rd",
    "city": "Columbus",
    "state": "OH",
    "country": "US",
    "lat": 40.002,
    "lon": -83.015,
    "calculation_method": "ISNA",
    "timezone": "America/New_York",
}


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _token(
    client: AsyncClient,
    *,
    email: str,
    password: str = _PASSWORD,
) -> str:
    """Sign up a fresh masjid-less operator and return their JWT."""
    await client.post("/api/auth/signup", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"login failed: {resp.text}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, token: str, **overrides: object):
    """POST /api/masjids with _MASJID_BODY merged with any overrides."""
    return await client.post(
        "/api/masjids",
        json={**_MASJID_BODY, **overrides},
        headers=_auth(token),
    )


async def _registered(
    client: AsyncClient, *, email: str
) -> tuple[str, str]:
    """Sign up operator, register masjid, return (masjid_id, scoped_token)."""
    tok = await _token(client, email=email)
    resp = await _register(client, tok)
    assert resp.status_code == 201, f"registration failed: {resp.text}"
    return resp.json()["id"], resp.json()["access_token"]


# ── Registration ──────────────────────────────────────────────────────────────


async def test_register_masjid_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/masjids", json=_MASJID_BODY)
    assert resp.status_code == 401


async def test_register_masjid_authenticated_no_masjid_returns_201(
    client: AsyncClient,
) -> None:
    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201


async def test_register_masjid_persists_to_db(
    client: AsyncClient, db: AsyncSession
) -> None:
    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201

    masjid_id = UUID(resp.json()["id"])
    row = (
        await db.execute(select(Masjid).where(Masjid.id == masjid_id))
    ).scalar_one_or_none()
    assert row is not None
    assert row.name == _MASJID_BODY["name"]
    assert row.city == _MASJID_BODY["city"]
    assert row.state == _MASJID_BODY["state"]


async def test_register_masjid_creates_owner_role(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.masjid import MasjidOperatorRole  # does not exist yet

    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201

    masjid_id = UUID(resp.json()["id"])
    role = (
        await db.execute(
            select(MasjidOperatorRole).where(
                MasjidOperatorRole.masjid_id == masjid_id
            )
        )
    ).scalar_one_or_none()
    assert role is not None
    assert role.role == "owner"


async def test_register_masjid_updates_operator_masjid_id(
    client: AsyncClient, db: AsyncSession
) -> None:
    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201

    masjid_id = UUID(resp.json()["id"])
    op = (
        await db.execute(
            select(OperatorAccount).where(OperatorAccount.email == _OP_A)
        )
    ).scalar_one_or_none()
    assert op is not None
    await db.refresh(op)
    assert op.masjid_id == masjid_id


async def test_register_masjid_response_contains_scoped_token(
    client: AsyncClient,
) -> None:
    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201

    data = resp.json()
    assert "access_token" in data, "response must include a fresh scoped access_token"
    payload = jwt.decode(
        data["access_token"], settings.secret_key, algorithms=["HS256"]
    )
    assert payload.get("masjid_id") == data["id"]


async def test_register_masjid_second_attempt_by_same_operator_returns_409(
    client: AsyncClient,
) -> None:
    tok = await _token(client, email=_OP_A)
    first = await _register(client, tok)
    assert first.status_code == 201

    # Use the scoped token returned by first registration
    scoped_tok = first.json()["access_token"]
    second = await _register(client, scoped_tok, name="Some Other Masjid")
    assert second.status_code == 409


async def test_register_masjid_blank_name_returns_422(client: AsyncClient) -> None:
    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok, name="")
    assert resp.status_code == 422


async def test_register_masjid_invalid_timezone_returns_422(
    client: AsyncClient,
) -> None:
    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok, timezone="Not/A/Valid/Timezone")
    assert resp.status_code == 422


async def test_register_masjid_duplicate_active_name_city_state_returns_409(
    client: AsyncClient,
) -> None:
    tok_a = await _token(client, email=_OP_A)
    first = await _register(client, tok_a)
    assert first.status_code == 201

    # Different operator, same (name, city, state) as an active masjid → 409
    tok_b = await _token(client, email=_OP_B)
    second = await _register(client, tok_b)  # identical _MASJID_BODY
    assert second.status_code == 409


async def test_register_masjid_duplicate_of_archived_returns_201(
    client: AsyncClient,
) -> None:
    # Operator A registers then archives
    masjid_id, scoped_tok_a = await _registered(client, email=_OP_A)
    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok_a)
    )
    assert archive.status_code == 200

    # Operator B may now claim the same identity — soft-deleted row must not block it
    tok_b = await _token(client, email=_OP_B)
    second = await _register(client, tok_b)  # same (name, city, state)
    assert second.status_code == 201


# ── Archive / soft-delete ─────────────────────────────────────────────────────


async def test_archive_sets_deleted_at(
    client: AsyncClient, db: AsyncSession
) -> None:
    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    resp = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert resp.status_code == 200

    row = (
        await db.execute(select(Masjid).where(Masjid.id == UUID(masjid_id)))
    ).scalar_one_or_none()
    assert row is not None
    await db.refresh(row)
    assert row.deleted_at is not None


async def test_archived_masjid_excluded_from_name_search(
    client: AsyncClient,
) -> None:
    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200

    resp = await client.get("/api/masjids/search", params={"q": _MASJID_BODY["name"]})
    assert resp.status_code == 200
    assert masjid_id not in [m["id"] for m in resp.json()]


async def test_archived_masjid_excluded_from_city_search(
    client: AsyncClient,
) -> None:
    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200

    resp = await client.get(
        "/api/masjids/search", params={"city": _MASJID_BODY["city"]}
    )
    assert resp.status_code == 200
    assert masjid_id not in [m["id"] for m in resp.json()]


async def test_archived_masjid_excluded_from_near_me_search(
    client: AsyncClient,
) -> None:
    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200

    resp = await client.get(
        "/api/masjids/search",
        params={"lat": _MASJID_BODY["lat"], "lon": _MASJID_BODY["lon"]},
    )
    assert resp.status_code == 200
    assert masjid_id not in [m["id"] for m in resp.json()]


async def test_restore_clears_deleted_at(
    client: AsyncClient, db: AsyncSession
) -> None:
    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    await client.delete(f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok))

    resp = await client.post(
        f"/api/masjids/{masjid_id}/restore", headers=_auth(scoped_tok)
    )
    assert resp.status_code == 200

    row = (
        await db.execute(select(Masjid).where(Masjid.id == UUID(masjid_id)))
    ).scalar_one_or_none()
    assert row is not None
    await db.refresh(row)
    assert row.deleted_at is None


async def test_restore_masjid_reappears_in_search(client: AsyncClient) -> None:
    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    await client.delete(f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok))
    restore = await client.post(
        f"/api/masjids/{masjid_id}/restore", headers=_auth(scoped_tok)
    )
    assert restore.status_code == 200

    resp = await client.get("/api/masjids/search", params={"q": _MASJID_BODY["name"]})
    assert resp.status_code == 200
    assert masjid_id in [m["id"] for m in resp.json()]


# ── Audit log ─────────────────────────────────────────────────────────────────


async def test_create_writes_audit_row(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.audit import MasjidAuditLog  # does not exist yet

    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201

    masjid_id = UUID(resp.json()["id"])
    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == masjid_id,
                MasjidAuditLog.action == "create",
            )
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_update_writes_audit_row_with_old_and_new_values(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.audit import MasjidAuditLog  # does not exist yet

    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    patch = await client.patch(
        f"/api/masjids/{masjid_id}",
        json={"name": "Masjid Al-Huda Renamed"},
        headers=_auth(scoped_tok),
    )
    assert patch.status_code == 200

    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == UUID(masjid_id),
                MasjidAuditLog.action == "update",
            )
        )
    ).scalars().all()
    assert len(rows) == 1
    log = rows[0]
    assert log.old_values is not None
    assert log.new_values is not None
    assert log.old_values.get("name") == _MASJID_BODY["name"]
    assert log.new_values.get("name") == "Masjid Al-Huda Renamed"


async def test_archive_writes_audit_row(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.audit import MasjidAuditLog  # does not exist yet

    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200

    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == UUID(masjid_id),
                MasjidAuditLog.action == "archive",
            )
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_restore_writes_audit_row(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.audit import MasjidAuditLog  # does not exist yet

    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    await client.delete(f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok))
    restore = await client.post(
        f"/api/masjids/{masjid_id}/restore", headers=_auth(scoped_tok)
    )
    assert restore.status_code == 200

    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == UUID(masjid_id),
                MasjidAuditLog.action == "restore",
            )
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_ownership_change_writes_audit_row(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.audit import MasjidAuditLog  # does not exist yet

    tok = await _token(client, email=_OP_A)
    resp = await _register(client, tok)
    assert resp.status_code == 201

    masjid_id = UUID(resp.json()["id"])
    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == masjid_id,
                MasjidAuditLog.action == "ownership_change",
            )
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_audit_rows_survive_archival(
    client: AsyncClient, db: AsyncSession
) -> None:
    from mubeen.db.models.audit import MasjidAuditLog  # does not exist yet

    masjid_id, scoped_tok = await _registered(client, email=_OP_A)

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200

    # The 'create', 'ownership_change', and 'archive' rows must all still exist
    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == UUID(masjid_id)
            )
        )
    ).scalars().all()
    actions = {r.action for r in rows}
    assert "create" in actions
    assert "ownership_change" in actions
    assert "archive" in actions
