"""WebSocket routes for the live khutbah captioning transport (MB-011/MB-012).

Transport contract: the hub transports BroadcastMessage events as opaque ordered
frames. It does NOT deduplicate, replace partials, or interpret sequence_number.
Partial/final replacement and ordering for display belong to MB-017.

Deployment constraint: until Redis pub/sub is introduced (MB-022), this backend
must run exactly ONE Uvicorn worker and ONE ECS Fargate replica. The in-memory
hub AND the _active_publishers set are not shared across OS processes.

Session constraint (MB-012): the publish socket requires a live KhutbahSession.
Operators must POST /khutbah/{masjid_id}/start before connecting a publisher.
"""

from __future__ import annotations

import asyncio
import datetime
import json
from uuid import UUID, uuid4

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import (
    OperatorTokenError,
    verify_operator_for_masjid,
    verify_operator_token_for_masjid,
)
from mubeen.db.models.khutbah import KhutbahSegment, KhutbahSession
from mubeen.db.session import SessionLocal, get_session
from mubeen.schemas.khutbah import (
    BroadcastMessage,
    PublishFrame,
    StartSessionResponse,
    StopSessionResponse,
)
from mubeen.services.broadcast import hub
from mubeen.services.khutbah import get_live_session, persist_final_segment
from mubeen.services.transcription import get_transcriber

log = structlog.get_logger()
router = APIRouter(prefix="/khutbah", tags=["khutbah"])
_bearer = HTTPBearer()

# In-memory single-publisher registry. One entry per masjid that currently has
# a connected publisher. This is a single-process invariant — the Redis swap-in
# point for multi-replica scaling is MB-022 (same as the hub).
_active_publishers: set[UUID] = set()


# ── Session lifecycle (HTTP) ───────────────────────────────────────────────────


@router.post(
    "/{masjid_id}/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(  # noqa: B008
    masjid_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> StartSessionResponse:
    """Open a live khutbah session for a masjid.

    Only one live session per masjid is allowed. Operators must call this
    before connecting a publish socket — the socket checks for a live session
    and closes 1008 if none exists.
    """
    verify_operator_for_masjid(credentials, masjid_id)

    existing = await get_live_session(db, masjid_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A live session already exists for this masjid",
        )

    session_row = KhutbahSession(id=uuid4(), masjid_id=masjid_id, status="live")
    db.add(session_row)
    await db.commit()
    log.info("session_started", masjid_id=str(masjid_id), session_id=str(session_row.id))
    return StartSessionResponse(
        session_id=session_row.id,
        masjid_id=masjid_id,
        status=session_row.status,
        started_at=session_row.started_at,
    )


@router.post("/{masjid_id}/stop", response_model=StopSessionResponse)
async def stop_session(  # noqa: B008
    masjid_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> StopSessionResponse:
    """Close the live khutbah session for a masjid.

    The khutbah is already saved: every finalized frame was persisted as a
    khutbah_segments row during the session (MB-012 Deliverable 3). This
    endpoint does NOT write a separate snapshot — "save the entire khutbah"
    (SPEC §5.7) is satisfied by those per-frame segment rows.
    """
    verify_operator_for_masjid(credentials, masjid_id)

    session_row = await get_live_session(db, masjid_id)
    if session_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No live session found for this masjid",
        )

    session_row.status = "completed"
    session_row.ended_at = datetime.datetime.now(datetime.UTC)
    await db.commit()
    log.info("session_stopped", masjid_id=str(masjid_id), session_id=str(session_row.id))
    return StopSessionResponse(
        session_id=session_row.id,
        status=session_row.status,
        ended_at=session_row.ended_at,
    )


# ── Publish socket (WebSocket) ─────────────────────────────────────────────────


@router.websocket("/{masjid_id}/publish")
async def publish(websocket: WebSocket, masjid_id: UUID) -> None:
    """Operator-authenticated ingest socket (MB-011 transport + MB-012 session gate).

    Auth: read ?token= query param (browsers cannot set Authorization headers on
    WebSocket connections). Accept first, then authenticate — this ensures a
    consistent WS close frame (1008) rather than an HTTP 4xx handshake rejection.

    Session gate: the operator must have started a live session via POST /start
    before connecting. If no live session exists, the socket closes 1008.

    Publisher exclusivity: only one publisher per masjid is allowed at a time.
    A second connect attempt closes 1008. Exclusivity is released in the finally
    block when the first publisher disconnects.

    Persistence: only finalized frames (is_partial=False) are written to
    khutbah_segments. Partials are broadcast-only. Each write uses a short
    async with SessionLocal() block to avoid pinning a DB connection for the
    full duration of a live khutbah.
    """
    await websocket.accept()

    # 1. Auth — must come first; consistent with MB-011 accept-then-auth pattern.
    token = websocket.query_params.get("token", "")
    try:
        operator_id = verify_operator_token_for_masjid(token, masjid_id)
    except OperatorTokenError:
        log.warning("publisher_rejected", masjid_id=str(masjid_id))
        await websocket.close(code=1008)
        return

    # 2. Session gate — short DB block; must not pin a connection for the session.
    async with SessionLocal() as db:
        session_row = await get_live_session(db, masjid_id)

    if session_row is None:
        log.warning("publisher_rejected_no_session", masjid_id=str(masjid_id))
        await websocket.close(code=1008)
        return

    session_id = session_row.id

    # 3. Publisher exclusivity — in-memory, single-process (Redis swap-in: MB-022).
    if masjid_id in _active_publishers:
        log.warning("publisher_rejected_duplicate", masjid_id=str(masjid_id))
        await websocket.close(code=1008)
        return

    _active_publishers.add(masjid_id)
    log.info(
        "publisher_connected",
        masjid_id=str(masjid_id),
        operator_id=str(operator_id),
        session_id=str(session_id),
    )

    try:
        while True:
            try:
                text = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                data = json.loads(text)
                frame = PublishFrame.model_validate(data)
            except (json.JSONDecodeError, ValidationError):
                log.warning("publisher_invalid_frame", masjid_id=str(masjid_id))
                await websocket.close(code=1008)
                return

            if not frame.is_partial:
                await persist_final_segment(session_id, frame.sequence_number, frame.arabic_text)
                log.debug(
                    "segment_persisted",
                    masjid_id=str(masjid_id),
                    session_id=str(session_id),
                    sequence_number=frame.sequence_number,
                )

            message = BroadcastMessage(
                masjid_id=masjid_id,
                sequence_number=frame.sequence_number,
                arabic_text=frame.arabic_text,
                is_partial=frame.is_partial,
            )
            hub.publish(masjid_id, message)
            log.debug(
                "frame_published",
                masjid_id=str(masjid_id),
                sequence_number=frame.sequence_number,
                subscriber_count=hub.subscriber_count(masjid_id),
            )
    finally:
        _active_publishers.discard(masjid_id)
        log.info("publisher_disconnected", masjid_id=str(masjid_id))


# ── Subscriber socket (WebSocket) ─────────────────────────────────────────────


@router.websocket("/{masjid_id}/live")
async def live(websocket: WebSocket, masjid_id: UUID) -> None:
    """Public subscriber socket — no auth required.

    Reconnect contract: no replay of missed frames. A reconnecting subscriber
    resumes from the moment it re-subscribes; backfill/replay is an MB-017
    display concern once sessions and persistence exist.

    Disconnect detection: asyncio.wait races a send task (await queue.get())
    against a receive task (await websocket.receive()) so an idle client that
    closes without sending data is detected promptly rather than only on the
    next outbound send.
    """
    await websocket.accept()
    queue = hub.subscribe(masjid_id)
    log.info(
        "subscriber_connected",
        masjid_id=str(masjid_id),
        subscriber_count=hub.subscriber_count(masjid_id),
    )

    try:
        while True:
            send_task = asyncio.create_task(queue.get(), name="ws_send")
            recv_task = asyncio.create_task(websocket.receive(), name="ws_recv")

            done, pending = await asyncio.wait(
                {send_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            await asyncio.gather(*done, return_exceptions=True)

            disconnected = False

            if recv_task in done:
                if recv_task.cancelled():
                    disconnected = True
                else:
                    exc = recv_task.exception()
                    if exc is not None:
                        if not isinstance(exc, (WebSocketDisconnect, asyncio.CancelledError)):
                            log.error(
                                "subscriber_recv_error",
                                masjid_id=str(masjid_id),
                                error=str(exc),
                            )
                        disconnected = True
                    else:
                        result = recv_task.result()
                        if (
                            isinstance(result, dict)
                            and result.get("type") == "websocket.disconnect"
                        ):
                            disconnected = True

            if send_task in done and not disconnected:
                if send_task.cancelled():
                    pass
                else:
                    exc = send_task.exception()
                    if exc is not None:
                        if not isinstance(exc, asyncio.CancelledError):
                            log.error(
                                "subscriber_queue_error",
                                masjid_id=str(masjid_id),
                                error=str(exc),
                            )
                        disconnected = True
                    else:
                        message: BroadcastMessage = send_task.result()
                        try:
                            await websocket.send_json(message.model_dump(mode="json"))
                        except WebSocketDisconnect:
                            disconnected = True
                        except Exception as exc:  # noqa: BLE001
                            log.error(
                                "subscriber_send_error",
                                masjid_id=str(masjid_id),
                                error=str(exc),
                            )
                            disconnected = True

            if disconnected:
                break

    finally:
        hub.unsubscribe(masjid_id, queue)
        log.info(
            "subscriber_disconnected",
            masjid_id=str(masjid_id),
            subscriber_count=hub.subscriber_count(masjid_id),
        )


# ── Audio ingest socket (WebSocket) ───────────────────────────────────────────

_MAX_RECONNECTS = 3
_RECONNECT_BACKOFF = [1.0, 2.0, 4.0]


@router.websocket("/{masjid_id}/audio")
async def audio(websocket: WebSocket, masjid_id: UUID) -> None:
    """Operator audio ingest: mic bytes → Deepgram → broadcast + persist (MB-013).

    SPEC §5 resilience contract:
    - Deepgram drops mid-session: the result pump exhausts; the route retries
      start() up to _MAX_RECONNECTS times with exponential backoff without
      closing the operator's audio WS. If all retries fail, the socket is closed
      with code 1011 (server error) so the client knows to reconnect; the session
      row stays live so a fresh connect is accepted.
    - Silence: result pump simply awaits next item. No timeout. Deepgram keepalive
      (KeepAlive frames) is sent automatically by the SDK; no special handling here.
    - Operator audio WS drops: WebSocketDisconnect in the audio pump exits cleanly
      via the finally block; _active_publishers is released; session stays live.

    Sequence-number ownership: the SERVER assigns sequence_number here (monotonic,
    starting from max-persisted+1 at connect). Unlike the text /publish path where
    the publisher supplies it, Deepgram utterances have no client sequence — the
    server owns ordering. Interims and the final that replaces them share a
    sequence_number (non-decreasing); seq increments only after each final is
    persisted.
    """
    await websocket.accept()

    # 1. Auth — accept-then-auth-then-1008 pattern.
    token = websocket.query_params.get("token", "")
    try:
        operator_id = verify_operator_token_for_masjid(token, masjid_id)
    except OperatorTokenError:
        log.warning("audio_publisher_rejected", masjid_id=str(masjid_id))
        await websocket.close(code=1008)
        return

    # 2. Session gate.
    async with SessionLocal() as db:
        session_row = await get_live_session(db, masjid_id)
    if session_row is None:
        log.warning("audio_publisher_rejected_no_session", masjid_id=str(masjid_id))
        await websocket.close(code=1008)
        return
    session_id = session_row.id

    # 3. Publisher exclusivity — same set as text /publish (only one publisher per masjid).
    if masjid_id in _active_publishers:
        log.warning("audio_publisher_rejected_duplicate", masjid_id=str(masjid_id))
        await websocket.close(code=1008)
        return

    _active_publishers.add(masjid_id)
    log.info(
        "audio_publisher_connected",
        masjid_id=str(masjid_id),
        operator_id=str(operator_id),
        session_id=str(session_id),
    )

    # Determine starting sequence_number from max already persisted for this session.
    async with SessionLocal() as db:
        max_seq = (
            await db.execute(
                sa_select(func.max(KhutbahSegment.sequence_number)).where(
                    KhutbahSegment.session_id == session_id
                )
            )
        ).scalar_one_or_none()
    seq = (max_seq or 0) + 1

    try:
        # transcriber_ref lets the audio pump reach the current transcriber across
        # reconnect attempts without a nonlocal rebind.
        transcriber_ref: list = [None]

        async def _audio_pump() -> None:
            """Forward mic bytes to the active transcriber until the WS closes."""
            try:
                while True:
                    try:
                        chunk = await websocket.receive_bytes()
                    except WebSocketDisconnect:
                        break
                    if transcriber_ref[0] is not None:
                        await transcriber_ref[0].send_audio(chunk)
            except asyncio.CancelledError:
                pass  # cancelled by outer cleanup — not an error

        # audio_task runs for the ENTIRE lifetime of the operator WebSocket.
        # It is NOT cancelled between reconnect attempts; only cancelled in cleanup.
        audio_task = asyncio.create_task(_audio_pump())

        reconnect_ok = True
        for attempt in range(_MAX_RECONNECTS + 1):
            if audio_task.done():
                break  # operator disconnected

            t = get_transcriber()
            transcriber_ref[0] = t

            try:
                await t.start()
                log.info(
                    "transcriber_started",
                    masjid_id=str(masjid_id),
                    attempt=attempt,
                )
            except Exception as exc:
                log.error(
                    "transcriber_start_failed",
                    masjid_id=str(masjid_id),
                    attempt=attempt,
                    error=str(exc),
                )
                reconnect_ok = False
                break

            async def _result_pump(transcriber=t) -> None:
                nonlocal seq
                async for r in transcriber.results():
                    message = BroadcastMessage(
                        masjid_id=masjid_id,
                        sequence_number=seq,
                        arabic_text=r.text,
                        is_partial=not r.is_final,
                    )
                    hub.publish(masjid_id, message)
                    if r.is_final:
                        await persist_final_segment(session_id, seq, r.text)
                        log.debug(
                            "segment_persisted",
                            masjid_id=str(masjid_id),
                            session_id=str(session_id),
                            sequence_number=seq,
                            confidence=r.confidence,
                        )
                        seq += 1

            result_task = asyncio.create_task(_result_pump())
            done, _pending = await asyncio.wait(
                {audio_task, result_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if audio_task in done:
                # Operator disconnected. Drain path: call close() FIRST so that
                # send_close_stream() triggers Deepgram to flush any buffered
                # finals. close() then waits for _run_listener to read them and
                # put the sentinel; result_task consumes those trailing finals and
                # exits naturally. Only then do we finish this attempt.
                await t.close()
                transcriber_ref[0] = None
                if result_task not in done:
                    await asyncio.gather(result_task, return_exceptions=True)
                break  # operator disconnected — do not reconnect

            # result_task finished first → Deepgram dropped; attempt reconnect.
            # Cancel result_task (it's already done or will be after cancel).
            result_task.cancel()
            await asyncio.gather(result_task, return_exceptions=True)

            # Log unexpected result_task errors (ignore CancelledError).
            if not result_task.cancelled():
                exc = result_task.exception()
                if exc is not None and not isinstance(exc, (asyncio.CancelledError, WebSocketDisconnect)):
                    log.error("result_pump_error", masjid_id=str(masjid_id), error=str(exc))

            await t.close()
            transcriber_ref[0] = None

            # result_task finished first → Deepgram dropped; attempt reconnect.
            if attempt < _MAX_RECONNECTS:
                backoff = _RECONNECT_BACKOFF[attempt]
                log.warning(
                    "transcriber_reconnect_attempt",
                    masjid_id=str(masjid_id),
                    attempt=attempt + 1,
                    backoff=backoff,
                )
                # Race backoff against audio_task: if operator disconnects during
                # the wait we detect it immediately instead of sleeping the full interval.
                sleep_task = asyncio.create_task(asyncio.sleep(backoff))
                done2, _ = await asyncio.wait(
                    {audio_task, sleep_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                sleep_task.cancel()
                await asyncio.gather(sleep_task, return_exceptions=True)
                if audio_task in done2:
                    break  # operator disconnected during backoff
            else:
                log.error(
                    "transcriber_reconnect_failed",
                    masjid_id=str(masjid_id),
                    max_attempts=_MAX_RECONNECTS,
                )
                reconnect_ok = False
                break

        # If audio_task is still running: either we gave up on reconnects or we
        # need to wait for the operator to disconnect before releasing the slot.
        if not audio_task.done():
            if not reconnect_ok:
                # Notify operator then wait for clean disconnect.
                try:
                    await websocket.close(code=1011)
                except Exception:
                    pass
            await asyncio.gather(audio_task, return_exceptions=True)
        else:
            await asyncio.gather(audio_task, return_exceptions=True)

    finally:
        _active_publishers.discard(masjid_id)
        log.info("audio_publisher_disconnected", masjid_id=str(masjid_id))
