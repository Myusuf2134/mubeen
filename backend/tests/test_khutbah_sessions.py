"""HTTP lifecycle tests for MB-012 (session start/stop).

Covers: POST /khutbah/{masjid_id}/start and POST /khutbah/{masjid_id}/stop.
Reuses the conftest db/client/seed_masjid/seed_operator fixtures.
Written BEFORE implementation (tests-first gate).
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import create_operator_token
from mubeen.db.models.khutbah import KhutbahSession

# ── start ─────────────────────────────────────────────────────────────────────


async def test_start_session_returns_201(client, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    resp = await client.post(
        f"/api/khutbah/{seed_masjid.id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201


async def test_start_session_response_fields(client, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    resp = await client.post(
        f"/api/khutbah/{seed_masjid.id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = resp.json()
    assert body["status"] == "live"
    assert body["masjid_id"] == str(seed_masjid.id)
    assert "session_id" in body
    assert "started_at" in body


async def test_start_session_persists_row(client, db, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    resp = await client.post(
        f"/api/khutbah/{seed_masjid.id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = resp.json()["session_id"]
    row = (
        await db.execute(select(KhutbahSession).where(KhutbahSession.id == session_id))
    ).scalar_one_or_none()
    assert row is not None
    assert row.status == "live"
    assert row.masjid_id == seed_masjid.id


async def test_start_session_duplicate_returns_409(client, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"/api/khutbah/{seed_masjid.id}/start", headers=headers)
    resp = await client.post(f"/api/khutbah/{seed_masjid.id}/start", headers=headers)
    assert resp.status_code == 409


async def test_start_session_wrong_masjid_token_returns_403(client, seed_masjid) -> None:
    wrong_token = create_operator_token(uuid4(), uuid4())
    resp = await client.post(
        f"/api/khutbah/{seed_masjid.id}/start",
        headers={"Authorization": f"Bearer {wrong_token}"},
    )
    assert resp.status_code == 403


async def test_start_session_no_token_returns_401(client, seed_masjid) -> None:
    resp = await client.post(f"/api/khutbah/{seed_masjid.id}/start")
    assert resp.status_code == 401  # HTTPBearer returns 401 when no credentials present


# ── stop ──────────────────────────────────────────────────────────────────────


async def test_stop_session_returns_200(client, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"/api/khutbah/{seed_masjid.id}/start", headers=headers)
    resp = await client.post(f"/api/khutbah/{seed_masjid.id}/stop", headers=headers)
    assert resp.status_code == 200


async def test_stop_session_response_fields(client, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"/api/khutbah/{seed_masjid.id}/start", headers=headers)
    resp = await client.post(f"/api/khutbah/{seed_masjid.id}/stop", headers=headers)
    body = resp.json()
    assert body["status"] == "completed"
    assert "session_id" in body
    assert "ended_at" in body


async def test_stop_session_updates_row(client, db, seed_masjid, seed_operator) -> None:
    _, token = seed_operator
    headers = {"Authorization": f"Bearer {token}"}
    start_resp = await client.post(f"/api/khutbah/{seed_masjid.id}/start", headers=headers)
    session_id = start_resp.json()["session_id"]

    await client.post(f"/api/khutbah/{seed_masjid.id}/stop", headers=headers)

    await db.refresh(
        (await db.execute(select(KhutbahSession).where(KhutbahSession.id == session_id))).scalar_one()
    )
    row = (
        await db.execute(select(KhutbahSession).where(KhutbahSession.id == session_id))
    ).scalar_one()
    assert row.status == "completed"
    assert row.ended_at is not None


async def test_stop_session_no_live_session_returns_404(
    client, seed_masjid, seed_operator
) -> None:
    _, token = seed_operator
    resp = await client.post(
        f"/api/khutbah/{seed_masjid.id}/stop",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_stop_session_wrong_masjid_token_returns_403(client, seed_masjid) -> None:
    wrong_token = create_operator_token(uuid4(), uuid4())
    resp = await client.post(
        f"/api/khutbah/{seed_masjid.id}/stop",
        headers={"Authorization": f"Bearer {wrong_token}"},
    )
    assert resp.status_code == 403


# ── get_live_session unit ─────────────────────────────────────────────────────


async def test_get_live_session_returns_live_row(db: AsyncSession, seed_masjid) -> None:
    from mubeen.services.khutbah import get_live_session

    ks = KhutbahSession(masjid_id=seed_masjid.id, status="live")
    db.add(ks)
    await db.flush()

    result = await get_live_session(db, seed_masjid.id)
    assert result is not None
    assert result.id == ks.id
    assert result.status == "live"


async def test_get_live_session_ignores_completed_and_aborted(
    db: AsyncSession, seed_masjid
) -> None:
    from mubeen.services.khutbah import get_live_session

    db.add(KhutbahSession(masjid_id=seed_masjid.id, status="completed"))
    db.add(KhutbahSession(masjid_id=seed_masjid.id, status="aborted"))
    await db.flush()

    result = await get_live_session(db, seed_masjid.id)
    assert result is None
