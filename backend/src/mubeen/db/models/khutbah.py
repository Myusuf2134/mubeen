from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mubeen.db.base import Base

if TYPE_CHECKING:
    from mubeen.db.models.masjid import Masjid


class KhutbahSession(Base):
    __tablename__ = "khutbah_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    masjid_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("masjids.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # live | completed | aborted
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="live")

    masjid: Mapped[Masjid] = relationship("Masjid", back_populates="khutbah_sessions")
    segments: Mapped[list[KhutbahSegment]] = relationship(
        "KhutbahSegment",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="KhutbahSegment.sequence_number",
    )


class KhutbahSegment(Base):
    """One finalized Deepgram utterance, after Qur'an matching and translation."""

    __tablename__ = "khutbah_segments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("khutbah_sessions.id", ondelete="CASCADE"), nullable=False
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    arabic_text: Mapped[str] = mapped_column(Text, nullable=False)
    english_text: Mapped[str | None] = mapped_column(Text)
    # plain_speech | quran | hadith
    segment_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="plain_speech")
    # Set when segment_type = "quran"
    quran_surah: Mapped[int | None] = mapped_column(Integer)
    quran_ayah: Mapped[int | None] = mapped_column(Integer)
    # True while the utterance is still being refined (Deepgram partial); False once finalized
    is_partial: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[KhutbahSession] = relationship("KhutbahSession", back_populates="segments")
