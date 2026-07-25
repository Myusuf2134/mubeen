from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mubeen.db.base import Base

if TYPE_CHECKING:
    from mubeen.db.models.khutbah import KhutbahSession
    from mubeen.db.models.operator import OperatorAccount


class Masjid(Base):
    __tablename__ = "masjids"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, server_default="US")
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    # Calculation method key (e.g. "ISNA", "MWL") — resolved to adhanpy params at query time
    calculation_method: Mapped[str] = mapped_column(String(50), nullable=False, server_default="ISNA")
    phone: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(500))
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    operator_accounts: Mapped[list[OperatorAccount]] = relationship(
        "OperatorAccount", back_populates="masjid", cascade="all, delete-orphan"
    )
    iqamah_times: Mapped[list[IqamahTime]] = relationship(
        "IqamahTime", back_populates="masjid", cascade="all, delete-orphan"
    )
    jumuah_times: Mapped[list[JumuahTime]] = relationship(
        "JumuahTime",
        back_populates="masjid",
        cascade="all, delete-orphan",
        order_by="JumuahTime.sort_order",
    )
    khutbah_sessions: Mapped[list[KhutbahSession]] = relationship(
        "KhutbahSession", back_populates="masjid", cascade="all, delete-orphan"
    )


class IqamahTime(Base):
    """Per-prayer iqamah time for a masjid.

    Exactly one of minutes_after_adhan or fixed_time must be set.
    fixed_time takes precedence when both are present.
    """

    __tablename__ = "iqamah_times"
    __table_args__ = (UniqueConstraint("masjid_id", "prayer", name="uq_iqamah_masjid_prayer"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    masjid_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("masjids.id", ondelete="CASCADE"), nullable=False
    )
    # fajr | dhuhr | asr | maghrib | isha
    prayer: Mapped[str] = mapped_column(String(20), nullable=False)
    minutes_after_adhan: Mapped[int | None] = mapped_column(Integer)
    fixed_time: Mapped[time | None] = mapped_column(Time)

    masjid: Mapped[Masjid] = relationship("Masjid", back_populates="iqamah_times")


class JumuahTime(Base):
    """One Jumu'ah slot for a masjid. Variable-length — any number allowed."""

    __tablename__ = "jumuah_times"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    masjid_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("masjids.id", ondelete="CASCADE"), nullable=False
    )
    # Human-readable label, e.g. "First Jumu'ah" or "الجمعة الأولى"
    label: Mapped[str | None] = mapped_column(String(255))
    # BCP-47 language tag for the label, e.g. "en", "ar", "so"
    language: Mapped[str | None] = mapped_column(String(10))
    time: Mapped[time] = mapped_column(Time, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    masjid: Mapped[Masjid] = relationship("Masjid", back_populates="jumuah_times")


class MasjidOperatorRole(Base):
    """Authoritative join between a masjid and an operator, carrying a role label."""

    __tablename__ = "masjid_operator_roles"
    __table_args__ = (
        UniqueConstraint("masjid_id", "operator_id", name="uq_masjid_operator_role"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    masjid_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("masjids.id"), nullable=False
    )
    operator_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operator_accounts.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
