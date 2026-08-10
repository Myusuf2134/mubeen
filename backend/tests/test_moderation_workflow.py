"""MB-009: moderation workflow tests.

Written BEFORE implementation (TDD). All tests are expected to fail.

Failing reasons at time of writing
────────────────────────────────────
  test_new_masjid_defaults_to_pending
      Masjid has no moderation_status column; getattr returns sentinel "<missing>".

  test_pending_masjid_hidden_from_public_search
      search_masjids only filters deleted_at IS NULL; pending masjids are returned.

  test_pending_masjid_hidden_from_public_detail
      GET /api/masjids/{id} returns 200 for any existing row; no pending guard.

  test_non_admin_cannot_approve
  test_non_admin_cannot_reject
  test_non_admin_cannot_list_pending
      Endpoints do not exist; FastAPI returns 404, not 403.

  test_admin_can_approve_makes_masjid_visible
  test_admin_can_reject_hides_masjid_not_soft_deleted
  test_admin_pending_list_returns_pending_masjids
      Admin approve/reject/pending-list endpoints do not exist (404).

  test_approved_then_archived_independence
      Approve endpoint missing; fails on the approve status assertion.

  test_pending_plus_soft_deleted_independence
      moderation_status column missing; getattr returns sentinel "<missing>".

  test_approve_writes_audit_row
  test_reject_writes_audit_row
      Approve/reject endpoints do not exist; no audit rows written.

Implementation required to green this suite
────────────────────────────────────────────
1. Add moderation_status VARCHAR(20) NOT NULL DEFAULT 'pending' to masjids.
2. Filter moderation_status = 'approved' from search_masjids and get_masjid.
3. POST /api/admin/masjids/{id}/approve — is_admin guard, sets approved, audit row.
4. POST /api/admin/masjids/{id}/reject  — is_admin guard, sets rejected, audit row.
5. GET  /api/admin/masjids/pending      — is_admin guard, returns pending rows.
6. Alembic migration for the new column.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import create_operator_token
from mubeen.db.models.audit import MasjidAuditLog
from mubeen.db.models.masjid import Masjid
from mubeen.db.models.operator import OperatorAccount

# ── Shared constants ──────────────────────────────────────────────────────────

_PASSWORD = "Str0ng-Passw0rd!"

_MASJID_BODY: dict = {
    "name": "Masjid Al-Moderation",
    "address_line": "55 Test Ave",
    "city": "Houston",
    "state": "TX",
    "country": "US",
    "lat": 29.7604,
    "lon": -95.3698,
    "calculation_method": "ISNA",
    "timezone": "America/Chicago",
}


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _token(client: AsyncClient, *, email: str) -> str:
    """Sign up a fresh masjid-less operator and return their JWT."""
    await client.post("/api/auth/signup", json={"email": email, "password": _PASSWORD})
    resp = await client.post("/api/auth/login", json={"email": email, "password": _PASSWORD})
    assert resp.status_code == 200, f"login failed: {resp.text}"
    return resp.json()["access_token"]


async def _register(
    client: AsyncClient, token: str, **overrides: object
) -> tuple[str, str]:
    """POST /api/masjids, assert 201, return (masjid_id, scoped_token)."""
    resp = await client.post(
        "/api/masjids",
        json={**_MASJID_BODY, **overrides},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"registration failed: {resp.text}"
    data = resp.json()
    return data["id"], data["access_token"]


async def _seed_admin(db: AsyncSession) -> str:
    """Insert a platform admin directly via the shared db session and return a JWT.

    Shares the same AsyncSession as the client fixture so the row is visible
    to endpoint handlers without a separate commit.
    """
    import bcrypt

    admin = OperatorAccount(
        id=uuid4(),
        email="platform-admin@test.mubeen",
        hashed_password=bcrypt.hashpw(b"admin-only", bcrypt.gensalt(rounds=4)).decode(),
        is_admin=True,
    )
    db.add(admin)
    await db.flush()
    return create_operator_token(admin.id, None)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Default pending status ────────────────────────────────────────────────────


async def test_new_masjid_defaults_to_pending(
    client: AsyncClient, db: AsyncSession
) -> None:
    """A newly registered masjid must have moderation_status='pending'."""
    tok = await _token(client, email="mod-default@test.mubeen")
    masjid_id, _ = await _register(client, tok)

    row = (
        await db.execute(select(Masjid).where(Masjid.id == UUID(masjid_id)))
    ).scalar_one_or_none()
    assert row is not None
    await db.refresh(row)

    mod_status = getattr(row, "moderation_status", "<missing>")
    assert mod_status == "pending", (
        f"Expected moderation_status='pending', got {mod_status!r}. "
        "Add the moderation_status column to the Masjid model."
    )


# ── Pending masjids hidden from public endpoints ──────────────────────────────


async def test_pending_masjid_hidden_from_public_search(
    client: AsyncClient,
) -> None:
    """A pending masjid must not appear in any public search result."""
    tok = await _token(client, email="mod-hidden-search@test.mubeen")
    masjid_id, _ = await _register(client, tok)

    resp = await client.get("/api/masjids/search", params={"q": _MASJID_BODY["name"]})
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()]
    assert masjid_id not in ids, (
        "Pending masjid must not appear in public name search. "
        "Add moderation_status='approved' filter to search_masjids."
    )


async def test_pending_masjid_hidden_from_public_detail(
    client: AsyncClient,
) -> None:
    """GET /api/masjids/{id} must return 404 for a pending masjid."""
    tok = await _token(client, email="mod-hidden-detail@test.mubeen")
    masjid_id, _ = await _register(client, tok)

    resp = await client.get(f"/api/masjids/{masjid_id}")
    assert resp.status_code == 404, (
        f"Expected 404 for a pending masjid, got {resp.status_code}. "
        "Guard get_masjid against pending moderation_status."
    )


# ── Non-admin gets 403 ────────────────────────────────────────────────────────


async def test_non_admin_cannot_approve(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    """A non-admin operator must receive 403 when calling the approve endpoint."""
    _, token = seed_operator
    resp = await client.post(
        f"/api/admin/masjids/{seed_masjid.id}/approve",
        headers=_auth(token),
    )
    assert resp.status_code == 403, (
        f"Expected 403 for non-admin approve, got {resp.status_code}."
    )


async def test_non_admin_cannot_reject(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    """A non-admin operator must receive 403 when calling the reject endpoint."""
    _, token = seed_operator
    resp = await client.post(
        f"/api/admin/masjids/{seed_masjid.id}/reject",
        headers=_auth(token),
    )
    assert resp.status_code == 403, (
        f"Expected 403 for non-admin reject, got {resp.status_code}."
    )


async def test_non_admin_cannot_list_pending(
    client: AsyncClient,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    """A non-admin operator must receive 403 on the pending-list endpoint."""
    _, token = seed_operator
    resp = await client.get("/api/admin/masjids/pending", headers=_auth(token))
    assert resp.status_code == 403, (
        f"Expected 403 for non-admin pending list, got {resp.status_code}."
    )


# ── Admin approve ─────────────────────────────────────────────────────────────


async def test_admin_can_approve_makes_masjid_visible(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Approving a masjid must set moderation_status='approved' and expose it publicly."""
    admin_tok = await _seed_admin(db)
    op_tok = await _token(client, email="mod-approve@test.mubeen")
    masjid_id, _ = await _register(client, op_tok)

    resp = await client.post(
        f"/api/admin/masjids/{masjid_id}/approve",
        headers=_auth(admin_tok),
    )
    assert resp.status_code == 200, f"approve returned {resp.status_code}: {resp.text}"

    search = await client.get("/api/masjids/search", params={"q": _MASJID_BODY["name"]})
    assert search.status_code == 200
    ids = [m["id"] for m in search.json()]
    assert masjid_id in ids, "Approved masjid must appear in public search."


# ── Admin reject ──────────────────────────────────────────────────────────────


async def test_admin_can_reject_hides_masjid_not_soft_deleted(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Rejection must keep the masjid hidden and must NOT set deleted_at."""
    admin_tok = await _seed_admin(db)
    op_tok = await _token(client, email="mod-reject@test.mubeen")
    masjid_id, _ = await _register(client, op_tok)

    resp = await client.post(
        f"/api/admin/masjids/{masjid_id}/reject",
        headers=_auth(admin_tok),
    )
    assert resp.status_code == 200, f"reject returned {resp.status_code}: {resp.text}"

    # Must not appear in public search
    search = await client.get("/api/masjids/search", params={"q": _MASJID_BODY["name"]})
    assert search.status_code == 200
    ids = [m["id"] for m in search.json()]
    assert masjid_id not in ids, "Rejected masjid must not appear in public search."

    # Rejection is moderation, not deletion — deleted_at must stay NULL
    row = (
        await db.execute(select(Masjid).where(Masjid.id == UUID(masjid_id)))
    ).scalar_one_or_none()
    assert row is not None
    await db.refresh(row)
    assert row.deleted_at is None, (
        "Rejecting must not set deleted_at. "
        "moderation_status and deleted_at are independent dimensions."
    )


# ── Pending-list endpoint ─────────────────────────────────────────────────────


async def test_admin_pending_list_returns_pending_masjids(
    client: AsyncClient, db: AsyncSession
) -> None:
    """GET /api/admin/masjids/pending must list all pending masjids for an admin."""
    admin_tok = await _seed_admin(db)
    op_tok = await _token(client, email="mod-list@test.mubeen")
    masjid_id, _ = await _register(client, op_tok)

    resp = await client.get("/api/admin/masjids/pending", headers=_auth(admin_tok))
    assert resp.status_code == 200, f"pending list returned {resp.status_code}: {resp.text}"

    ids = [m["id"] for m in resp.json()]
    assert masjid_id in ids, (
        "Newly registered (pending) masjid must appear in /api/admin/masjids/pending."
    )


# ── Independence of moderation_status and deleted_at ─────────────────────────


async def test_approved_then_archived_independence(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Archiving an approved masjid must set deleted_at without reverting moderation_status."""
    admin_tok = await _seed_admin(db)
    op_tok = await _token(client, email="mod-approved-archive@test.mubeen")
    masjid_id, scoped_tok = await _register(client, op_tok)

    approve = await client.post(
        f"/api/admin/masjids/{masjid_id}/approve",
        headers=_auth(admin_tok),
    )
    assert approve.status_code == 200, f"approve failed: {approve.text}"

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200, f"archive failed: {archive.text}"

    row = (
        await db.execute(select(Masjid).where(Masjid.id == UUID(masjid_id)))
    ).scalar_one_or_none()
    assert row is not None
    await db.refresh(row)

    mod_status = getattr(row, "moderation_status", "<missing>")
    assert mod_status == "approved", (
        f"moderation_status must remain 'approved' after archiving; got {mod_status!r}."
    )
    assert row.deleted_at is not None, "deleted_at must be set after archiving."


async def test_pending_plus_soft_deleted_independence(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Soft-deleting a pending masjid must not change its moderation_status."""
    op_tok = await _token(client, email="mod-pending-delete@test.mubeen")
    masjid_id, scoped_tok = await _register(client, op_tok)

    archive = await client.delete(
        f"/api/masjids/{masjid_id}", headers=_auth(scoped_tok)
    )
    assert archive.status_code == 200, f"archive failed: {archive.text}"

    row = (
        await db.execute(select(Masjid).where(Masjid.id == UUID(masjid_id)))
    ).scalar_one_or_none()
    assert row is not None
    await db.refresh(row)

    mod_status = getattr(row, "moderation_status", "<missing>")
    assert mod_status == "pending", (
        f"Soft-deleting must not alter moderation_status; got {mod_status!r}."
    )
    assert row.deleted_at is not None, "deleted_at must be set after archiving."


# ── Audit rows for approve / reject ──────────────────────────────────────────


async def test_approve_writes_audit_row(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Approving a masjid must write exactly one MasjidAuditLog row with action='approve'."""
    admin_tok = await _seed_admin(db)
    op_tok = await _token(client, email="mod-audit-approve@test.mubeen")
    masjid_id, _ = await _register(client, op_tok)

    resp = await client.post(
        f"/api/admin/masjids/{masjid_id}/approve",
        headers=_auth(admin_tok),
    )
    assert resp.status_code == 200, f"approve failed: {resp.text}"

    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == UUID(masjid_id),
                MasjidAuditLog.action == "approve",
            )
        )
    ).scalars().all()
    assert len(rows) == 1, (
        f"Expected 1 audit row with action='approve', found {len(rows)}."
    )


async def test_reject_writes_audit_row(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Rejecting a masjid must write exactly one MasjidAuditLog row with action='reject'."""
    admin_tok = await _seed_admin(db)
    op_tok = await _token(client, email="mod-audit-reject@test.mubeen")
    masjid_id, _ = await _register(client, op_tok)

    resp = await client.post(
        f"/api/admin/masjids/{masjid_id}/reject",
        headers=_auth(admin_tok),
    )
    assert resp.status_code == 200, f"reject failed: {resp.text}"

    rows = (
        await db.execute(
            select(MasjidAuditLog).where(
                MasjidAuditLog.masjid_id == UUID(masjid_id),
                MasjidAuditLog.action == "reject",
            )
        )
    ).scalars().all()
    assert len(rows) == 1, (
        f"Expected 1 audit row with action='reject', found {len(rows)}."
    )
