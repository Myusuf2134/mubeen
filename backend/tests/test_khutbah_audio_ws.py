"""Audio WebSocket route tests (MB-013 Deliverable 3), FakeTranscriber injected.

All tests are deterministic — no Deepgram API key or network required.
The FakeTranscriber is injected by monkeypatching mubeen.api.khutbah.get_transcriber.
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import create_operator_token
from mubeen.api.khutbah import _active_publishers
from mubeen.db.models.khutbah import KhutbahSegment, KhutbahSession
from mubeen.db.models.masjid import Masjid
from mubeen.services.transcription import FakeTranscriber, TranscriptResult

from .ws_helpers import WebSocketDisconnect, ws_connect

# ── Fixture helpers ───────────────────────────────────────────────────────────


@pytest_asyncio.fixture(autouse=True)
async def reset_publishers() -> None:
    _active_publishers.clear()
    yield
    _active_publishers.clear()


@pytest_asyncio.fixture
async def audio_live_session(db: AsyncSession) -> tuple[UUID, str, UUID]:
    """Committed masjid + live KhutbahSession; returns (masjid_id, token, session_id)."""
    mid = uuid4()
    db.add(
        Masjid(
            id=mid,
            name="Audio Test Masjid",
            address_line="1 Audio Ave",
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


def _install_fake(monkeypatch, script: list[TranscriptResult]) -> FakeTranscriber:
    fake = FakeTranscriber(script)
    monkeypatch.setattr("mubeen.api.khutbah.get_transcriber", lambda: fake)
    return fake


# ── Auth / session gate ───────────────────────────────────────────────────────


async def test_audio_no_live_session_closes_1008(db: AsyncSession, monkeypatch) -> None:
    mid = uuid4()
    db.add(
        Masjid(
            id=mid,
            name="No Session Masjid",
            address_line="2 Main St",
            city="Chicago",
            state="IL",
            country="US",
            lat=41.8,
            lon=-87.6,
            calculation_method="ISNA",
            moderation_status="approved",
        )
    )
    await db.commit()
    token = create_operator_token(uuid4(), mid)
    _install_fake(monkeypatch, [])

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as ws:
            await ws.receive_json()
    assert exc_info.value.code == 1008


async def test_audio_wrong_masjid_token_closes_1008(audio_live_session, monkeypatch) -> None:
    mid, _token, _sid = audio_live_session
    wrong_token = create_operator_token(uuid4(), uuid4())
    _install_fake(monkeypatch, [])

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={wrong_token}") as ws:
            await ws.receive_json()
    assert exc_info.value.code == 1008


async def test_audio_invalid_token_closes_1008(audio_live_session, monkeypatch) -> None:
    mid, _token, _sid = audio_live_session
    _install_fake(monkeypatch, [])

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token=notavalidtoken") as ws:
            await ws.receive_json()
    assert exc_info.value.code == 1008


async def test_audio_while_publisher_active_closes_1008(audio_live_session, monkeypatch) -> None:
    mid, token, _sid = audio_live_session
    _active_publishers.add(mid)
    _install_fake(monkeypatch, [])

    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as ws:
            await ws.receive_json()
    assert exc_info.value.code == 1008


# ── Broadcast behaviour ───────────────────────────────────────────────────────


async def test_interim_result_broadcasts_as_partial(audio_live_session, monkeypatch) -> None:
    mid, token, _sid = audio_live_session
    script = [TranscriptResult(text="بسم", is_final=False)]
    _install_fake(monkeypatch, script)

    received = []
    # Open a subscriber before the publisher connects.
    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
            await pub.send_bytes(b"\x00" * 64)
            await asyncio.sleep(0.05)

        msg = await sub.receive_json()
        received.append(msg)

    assert len(received) == 1
    assert received[0]["is_partial"] is True
    assert received[0]["arabic_text"] == "بسم"


async def test_final_result_broadcasts_as_not_partial(audio_live_session, monkeypatch) -> None:
    mid, token, _sid = audio_live_session
    script = [TranscriptResult(text="بسم الله", is_final=True, confidence=0.99)]
    _install_fake(monkeypatch, script)

    received = []
    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
            await pub.send_bytes(b"\x00" * 64)
            await asyncio.sleep(0.05)

        msg = await sub.receive_json()
        received.append(msg)

    assert received[0]["is_partial"] is False
    assert received[0]["arabic_text"] == "بسم الله"


# ── Persistence behaviour ─────────────────────────────────────────────────────


async def test_final_result_persisted(audio_live_session, db: AsyncSession, monkeypatch) -> None:
    mid, token, session_id = audio_live_session
    script = [TranscriptResult(text="الحمد لله", is_final=True, confidence=0.97)]
    _install_fake(monkeypatch, script)

    async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
        await pub.send_bytes(b"\x00" * 64)
        await asyncio.sleep(0.1)

    # Refresh db view after route committed.
    await db.rollback()
    rows = (
        await db.execute(
            select(KhutbahSegment).where(KhutbahSegment.session_id == session_id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].arabic_text == "الحمد لله"
    assert rows[0].is_partial is False


async def test_interim_result_not_persisted(audio_live_session, db: AsyncSession, monkeypatch) -> None:
    mid, token, session_id = audio_live_session
    script = [TranscriptResult(text="الحمد", is_final=False)]
    _install_fake(monkeypatch, script)

    async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
        await pub.send_bytes(b"\x00" * 64)
        await asyncio.sleep(0.1)

    await db.rollback()
    rows = (
        await db.execute(
            select(KhutbahSegment).where(KhutbahSegment.session_id == session_id)
        )
    ).scalars().all()
    assert len(rows) == 0


async def test_persisted_segment_fields(audio_live_session, db: AsyncSession, monkeypatch) -> None:
    mid, token, session_id = audio_live_session
    script = [TranscriptResult(text="رب العالمين", is_final=True, confidence=0.95)]
    _install_fake(monkeypatch, script)

    async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
        await pub.send_bytes(b"\x00" * 64)
        await asyncio.sleep(0.1)

    await db.rollback()
    row = (
        await db.execute(
            select(KhutbahSegment).where(KhutbahSegment.session_id == session_id)
        )
    ).scalar_one()
    assert row.segment_type == "plain_speech"
    assert row.english_text is None
    assert row.is_partial is False


# ── Sequence number assignment ────────────────────────────────────────────────


async def test_sequence_number_monotonic(audio_live_session, db: AsyncSession, monkeypatch) -> None:
    mid, token, session_id = audio_live_session
    script = [
        TranscriptResult(text="فصل", is_final=False),
        TranscriptResult(text="فصل الأول", is_final=True, confidence=0.96),
        TranscriptResult(text="فصل الثاني", is_final=True, confidence=0.97),
    ]
    _install_fake(monkeypatch, script)

    received = []
    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
            await pub.send_bytes(b"\x00" * 64)
            await asyncio.sleep(0.15)

        for _ in range(3):
            msg = await sub.receive_json()
            received.append(msg)

    seqs = [m["sequence_number"] for m in received]
    # sequence numbers must be non-decreasing
    assert seqs == sorted(seqs)
    # the two finals must have different seq numbers
    finals = [m for m in received if not m["is_partial"]]
    assert len(finals) == 2
    assert finals[0]["sequence_number"] != finals[1]["sequence_number"]


async def test_sequence_resumes_from_max_persisted(
    audio_live_session, db: AsyncSession, monkeypatch
) -> None:
    mid, token, session_id = audio_live_session
    # Pre-seed a segment at seq=5.
    db.add(
        KhutbahSegment(
            session_id=session_id,
            sequence_number=5,
            arabic_text="قديم",
            is_partial=False,
            segment_type="plain_speech",
        )
    )
    await db.commit()

    script = [TranscriptResult(text="جديد", is_final=True, confidence=0.99)]
    _install_fake(monkeypatch, script)

    received = []
    async with ws_connect(f"/api/khutbah/{mid}/live") as sub:
        async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}") as pub:
            await pub.send_bytes(b"\x00" * 64)
            await asyncio.sleep(0.1)

        msg = await sub.receive_json()
        received.append(msg)

    assert received[0]["sequence_number"] == 6  # max_persisted(5) + 1


# ── Multi-masjid isolation ────────────────────────────────────────────────────


async def test_two_masjids_no_cross_contamination(db: AsyncSession, monkeypatch) -> None:
    def _make_masjid(name: str):
        mid = uuid4()
        db.add(
            Masjid(
                id=mid,
                name=name,
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
        ks = KhutbahSession(masjid_id=mid, status="live")
        db.add(ks)
        return mid, ks

    mid_a, ks_a = _make_masjid("Masjid A")
    mid_b, ks_b = _make_masjid("Masjid B")
    await db.commit()

    tok_a = create_operator_token(uuid4(), mid_a)
    tok_b = create_operator_token(uuid4(), mid_b)

    script_a = [TranscriptResult(text="نص أ", is_final=True, confidence=0.9)]
    script_b = [TranscriptResult(text="نص ب", is_final=True, confidence=0.9)]

    call_count = 0

    def _factory():
        nonlocal call_count
        call_count += 1
        return FakeTranscriber(script_a if call_count == 1 else script_b)

    monkeypatch.setattr("mubeen.api.khutbah.get_transcriber", _factory)

    async with ws_connect(f"/api/khutbah/{mid_a}/audio?token={tok_a}") as pub_a:
        async with ws_connect(f"/api/khutbah/{mid_b}/audio?token={tok_b}") as pub_b:
            await pub_a.send_bytes(b"\x00" * 64)
            await pub_b.send_bytes(b"\x00" * 64)
            await asyncio.sleep(0.15)

    await db.rollback()

    segs_a = (
        await db.execute(
            select(KhutbahSegment).where(KhutbahSegment.session_id == ks_a.id)
        )
    ).scalars().all()
    segs_b = (
        await db.execute(
            select(KhutbahSegment).where(KhutbahSegment.session_id == ks_b.id)
        )
    ).scalars().all()

    assert len(segs_a) == 1
    assert segs_a[0].arabic_text == "نص أ"
    assert len(segs_b) == 1
    assert segs_b[0].arabic_text == "نص ب"


# ── Publisher exclusivity lifecycle ──────────────────────────────────────────


async def test_disconnect_releases_active_publishers(
    audio_live_session, monkeypatch
) -> None:
    mid, token, _sid = audio_live_session
    _install_fake(monkeypatch, [])

    assert mid not in _active_publishers
    async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}"):
        await asyncio.sleep(0.05)  # let route reach _active_publishers.add()
        assert mid in _active_publishers
    # After disconnect, the slot must be free.
    assert mid not in _active_publishers


async def test_text_publisher_blocked_while_audio_active(
    audio_live_session, monkeypatch
) -> None:
    mid, token, _sid = audio_live_session
    _install_fake(monkeypatch, [])

    async with ws_connect(f"/api/khutbah/{mid}/audio?token={token}"):
        await asyncio.sleep(0.05)  # let audio route register in _active_publishers
        # Text publisher should be rejected since audio publisher holds the slot.
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with ws_connect(f"/api/khutbah/{mid}/publish?token={token}") as ws:
                await ws.receive_json()
        assert exc_info.value.code == 1008
