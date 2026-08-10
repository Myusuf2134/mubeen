"""Session-query helpers shared by the khutbah HTTP routes and WebSocket handler."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.db.models.khutbah import KhutbahSegment, KhutbahSession
from mubeen.db.session import SessionLocal


async def get_live_session(db: AsyncSession, masjid_id: UUID) -> KhutbahSession | None:
    """Return the single live KhutbahSession for a masjid, or None.

    Called from both the HTTP stop endpoint (via Depends(get_session)) and the
    publish WebSocket handler (via a short async with SessionLocal() block).
    """
    return (
        await db.execute(
            select(KhutbahSession).where(
                KhutbahSession.masjid_id == masjid_id,
                KhutbahSession.status == "live",
            )
        )
    ).scalar_one_or_none()


async def persist_final_segment(
    session_id: UUID,
    sequence_number: int,
    arabic_text: str,
) -> None:
    """Write one finalized KhutbahSegment (plain_speech, english_text=None).

    Uses a short async with SessionLocal() block — safe to call from a
    long-lived WS handler without pinning a connection for the session.
    """
    async with SessionLocal() as db:
        db.add(
            KhutbahSegment(
                session_id=session_id,
                sequence_number=sequence_number,
                arabic_text=arabic_text,
                is_partial=False,
                segment_type="plain_speech",
            )
        )
        await db.commit()
