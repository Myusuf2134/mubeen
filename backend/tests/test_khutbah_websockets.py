"""WebSocket integration tests for MB-011 (fan-out hub) and MB-012 (session gate).

Written BEFORE implementation (tests-first gate). Tests exercise the security-
critical boundary: operator auth + session gate + publisher exclusivity on the
publish socket, channel isolation, persistence, and clean disconnect/reconnect.

Transport note: httpx-ws + ASGITransport uses HTTP upgrade (http scope), which
FastAPI WebSocket routes do not respond to (they expect a websocket scope). This
file uses ws_helpers.ws_connect — a thin async ASGI client that speaks the ASGI
websocket protocol directly in the SAME event loop as the tests.
"""

from __future__ import annotations

import asyncio
import datetime
from uuid import UUID, uuid4

import jwt
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import create_operator_token
from mubeen.config import settings
from mubeen.db.models.khutbah import KhutbahSegment, KhutbahSession
from mubeen.db.models.masjid import Masjid

from .ws_helpers import WebSocketDisconnect, valid_frame, ws_connect

# ── Helpers ───────────────────────────────────────────────────────────────────

_ALGORITHM = "HS256"


def _expired_token(operator_id: UUID, masjid_id: UUID) -> str:
    payload = {
        "operator_id": str(operator_id),
        "masjid_id": str(masjid_id),
        "exp": datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_hub() -> None:
    """Wipe hub channels and active-publisher registry before and after each test."""
    from mubeen.api.khutbah import _active_publishers
    from mubeen.services.broadcast import hub

    _active_publishers.clear()
    hub._channels.clear()
    yield
    _active_publishers.clear()
    hub._channels.clear()


@pytest_asyncio.fixture
async def ws_live_session(db: AsyncSession) -> tuple[UUID, str, UUID]:
    """Committed masjid + live KhutbahSession visible to the WS handler's SessionLocal().

    Returns (masjid_id, operator_token, session_id). Requests db so the autouse
    db-fixture cleanup runs after the test.
    """
    mid = uuid4()
    db.add(
        Masjid(
            id=mid,
            name="WS Test Masjid",
            address_line="1 Main St",
            city="Chicago",
            state="IL",
            country="US",
            lat=41.8781,
            lon=-87.6298,
            calculation_method="ISNA",
            moderation_status="approved",
        )
    )
    ks = KhutbahSession(masjid_id=mid, status="live")
    db.add(ks)
    await db.commit()
    token = create_operator_token(uuid4(), mid)
    return mid, token, ks.id


# ── Publish / subscribe happy path ────────────────────────────────────────────


async def test_valid_token_publish_subscriber_receives(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json(valid_frame())

        data = await sub.receive_json()

    assert data["arabic_text"] == "بسم الله"


async def test_two_subscribers_both_receive_published_frame(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub1:
        async with ws_connect(f"/api/khutbah/{mid}/live") as sub2:
            async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
                await pub.send_json(valid_frame())

            data1 = await sub1.receive_json()
            data2 = await sub2.receive_json()

    assert data1["arabic_text"] == "بسم الله"
    assert data2["arabic_text"] == "بسم الله"


async def test_different_masjid_subscriber_receives_no_frame_within_timeout(
    ws_live_session,
) -> None:
    """Cross-masjid isolation: subscriber on B must never see frames published to A."""
    mid_a, token_a, _ = ws_live_session
    mid_b = uuid4()  # B exists only as a subscriber channel — no session required for /live

    async with ws_connect(f"/api/khutbah/{mid_b}/live") as sub_b:
        async with ws_connect(f"/api/khutbah/{mid_a}/publish?token={token_a}") as pub:
            await pub.send_json(valid_frame())
        await asyncio.sleep(0.05)

        with pytest.raises(TimeoutError):
            async with asyncio.timeout(1.0):
                await sub_b.receive_json()


# ── Auth failure → close 1008 ─────────────────────────────────────────────────
# Auth is checked before the session gate, so these tests need no live session.


async def test_wrong_masjid_token_closes_1008() -> None:
    mid = uuid4()
    wrong_token = create_operator_token(uuid4(), uuid4())

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={wrong_token}") as pub:
            await pub.receive_json()

    assert exc_info.value.code == 1008


async def test_invalid_token_closes_1008() -> None:
    mid = uuid4()

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token=not-a-jwt") as pub:
            await pub.receive_json()

    assert exc_info.value.code == 1008


async def test_expired_token_closes_1008() -> None:
    mid = uuid4()
    token = _expired_token(uuid4(), mid)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.receive_json()

    assert exc_info.value.code == 1008


# ── Session gate → close 1008 ─────────────────────────────────────────────────


async def test_publish_no_live_session_closes_1008() -> None:
    """No session → publish socket closes 1008 even with a valid auth token."""
    mid = uuid4()
    token = create_operator_token(uuid4(), mid)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.receive_json()

    assert exc_info.value.code == 1008


# ── Publisher exclusivity ─────────────────────────────────────────────────────


async def test_second_publisher_same_masjid_closes_1008(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}"):
        # Let pub1 finish its session DB query and register itself in _active_publishers.
        await asyncio.sleep(0.05)

        token2 = create_operator_token(uuid4(), mid)
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with ws_connect(f"/api/khutbah/{mid}/publish?token={token2}") as pub2:
                await pub2.receive_json()

        assert exc_info.value.code == 1008


async def test_publisher_exclusivity_released_after_disconnect(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}"):
        pass  # pub1 connects then disconnects

    # __aexit__ waits for the task to finish (which runs the finally block that
    # removes masjid_id from _active_publishers), so no extra sleep needed here.

    token2 = create_operator_token(uuid4(), mid)
    async with ws_connect(f"/api/khutbah/{mid}/publish?token={token2}"):
        pass  # pub2 accepted — exclusivity was released


# ── Malformed / invalid frames → close 1008 ───────────────────────────────────


async def test_bad_json_frame_closes_1008(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_text("not json at all {{{{")
            await pub.receive_json()

    assert exc_info.value.code == 1008


async def test_missing_arabic_text_closes_1008(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json({"sequence_number": 1})
            await pub.receive_json()

    assert exc_info.value.code == 1008


async def test_oversized_arabic_text_closes_1008(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json({"arabic_text": "ب" * 2001, "sequence_number": 1})
            await pub.receive_json()

    assert exc_info.value.code == 1008


async def test_undeclared_fields_rejected_extra_forbid_closes_1008(ws_live_session) -> None:
    """extra='forbid' on PublishFrame: undeclared fields close 1008 without broadcasting."""
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
                await pub.send_json(
                    {
                        "arabic_text": "test",
                        "sequence_number": 1,
                        "masjid_id": str(uuid4()),
                    }
                )
                await pub.receive_json()

        assert exc_info.value.code == 1008

        with pytest.raises(TimeoutError):
            async with asyncio.timeout(1.0):
                await sub.receive_json()


# ── Persistence — finalized frames ────────────────────────────────────────────


async def test_final_frame_persisted_as_segment(ws_live_session) -> None:
    mid, token, session_id = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json(valid_frame(seq=1, text="اَلْحَمْدُ لِلّٰه"))
        await sub.receive_json()

    from mubeen.db.session import SessionLocal

    async with SessionLocal() as db:
        segs = (
            await db.execute(
                select(KhutbahSegment).where(KhutbahSegment.session_id == session_id)
            )
        ).scalars().all()

    assert len(segs) == 1
    assert segs[0].arabic_text == "اَلْحَمْدُ لِلّٰه"
    assert segs[0].sequence_number == 1
    assert segs[0].is_partial is False


async def test_partial_frame_not_persisted_but_broadcast(ws_live_session) -> None:
    mid, token, session_id = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json(valid_frame(seq=1, text="partial text", is_partial=True))
        data = await sub.receive_json()

    assert data["arabic_text"] == "partial text"
    assert data["is_partial"] is True

    from mubeen.db.session import SessionLocal

    async with SessionLocal() as db:
        segs = (
            await db.execute(
                select(KhutbahSegment).where(KhutbahSegment.session_id == session_id)
            )
        ).scalars().all()

    assert len(segs) == 0


async def test_persisted_segment_has_plain_speech_and_null_english(ws_live_session) -> None:
    mid, token, session_id = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json(valid_frame(seq=7, text="الله أكبر"))
        await sub.receive_json()

    from mubeen.db.session import SessionLocal

    async with SessionLocal() as db:
        seg = (
            await db.execute(
                select(KhutbahSegment).where(KhutbahSegment.session_id == session_id)
            )
        ).scalar_one()

    assert seg.segment_type == "plain_speech"
    assert seg.english_text is None


async def test_two_masjids_concurrent_sessions_persist_to_own_sessions(
    db: AsyncSession,
) -> None:
    """Segments for masjid A never appear under masjid B's session and vice-versa."""
    mid_a, mid_b = uuid4(), uuid4()
    token_a = create_operator_token(uuid4(), mid_a)
    token_b = create_operator_token(uuid4(), mid_b)

    for mid in (mid_a, mid_b):
        db.add(
            Masjid(
                id=mid,
                name=f"Masjid {mid}",
                address_line="1 St",
                city="Chicago",
                state="IL",
                country="US",
                lat=41.0,
                lon=-87.0,
                calculation_method="ISNA",
                moderation_status="approved",
            )
        )
    ks_a = KhutbahSession(masjid_id=mid_a, status="live")
    ks_b = KhutbahSession(masjid_id=mid_b, status="live")
    db.add(ks_a)
    db.add(ks_b)
    await db.commit()

    async with ws_connect(f"/api/khutbah/{mid_a}/live") as sub_a:
        async with ws_connect(f"/api/khutbah/{mid_b}/live") as sub_b:
            async with ws_connect(f"/api/khutbah/{mid_a}/publish?token={token_a}") as pub_a:
                await pub_a.send_json(valid_frame(seq=1, text="Text A"))
            await asyncio.sleep(0.05)
            async with ws_connect(f"/api/khutbah/{mid_b}/publish?token={token_b}") as pub_b:
                await pub_b.send_json(valid_frame(seq=1, text="Text B"))

            data_a = await sub_a.receive_json()
            data_b = await sub_b.receive_json()

    assert data_a["arabic_text"] == "Text A"
    assert data_b["arabic_text"] == "Text B"

    from mubeen.db.session import SessionLocal

    async with SessionLocal() as fresh:
        segs_a = (
            await fresh.execute(
                select(KhutbahSegment).where(KhutbahSegment.session_id == ks_a.id)
            )
        ).scalars().all()
        segs_b = (
            await fresh.execute(
                select(KhutbahSegment).where(KhutbahSegment.session_id == ks_b.id)
            )
        ).scalars().all()

    assert len(segs_a) == 1 and segs_a[0].arabic_text == "Text A"
    assert len(segs_b) == 1 and segs_b[0].arabic_text == "Text B"


# ── Disconnect and reconnect ──────────────────────────────────────────────────
# These tests use /live only — no session gate, no DB needed.


async def test_disconnected_subscriber_count_returns_to_zero() -> None:
    from mubeen.services.broadcast import hub

    mid = uuid4()

    async with ws_connect(f"/api/khutbah/{mid}/live"):
        assert hub.subscriber_count(mid) == 1

    await asyncio.sleep(0.05)
    assert hub.subscriber_count(mid) == 0


async def test_idle_subscriber_disconnect_cleans_up() -> None:
    from mubeen.services.broadcast import hub

    mid = uuid4()

    async with ws_connect(f"/api/khutbah/{mid}/live"):
        assert hub.subscriber_count(mid) == 1

    await asyncio.sleep(0.05)
    assert hub.subscriber_count(mid) == 0


async def test_reconnect_creates_exactly_one_subscription() -> None:
    from mubeen.services.broadcast import hub

    mid = uuid4()

    async with ws_connect(f"/api/khutbah/{mid}/live"):
        assert hub.subscriber_count(mid) == 1

    await asyncio.sleep(0.05)
    assert hub.subscriber_count(mid) == 0

    async with ws_connect(f"/api/khutbah/{mid}/live"):
        assert hub.subscriber_count(mid) == 1

    await asyncio.sleep(0.05)
    assert hub.subscriber_count(mid) == 0


# ── Delivered-message shape ───────────────────────────────────────────────────


async def test_masjid_id_in_delivered_message_equals_url_channel(ws_live_session) -> None:
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json(valid_frame())

        data = await sub.receive_json()

    assert data["masjid_id"] == str(mid)


async def test_delivered_message_english_text_none_segment_type_plain_speech(
    ws_live_session,
) -> None:
    mid, token, _ = ws_live_session

    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as pub:
            await pub.send_json(valid_frame())

        data = await sub.receive_json()

    assert data["english_text"] is None
    assert data["segment_type"] == "plain_speech"
