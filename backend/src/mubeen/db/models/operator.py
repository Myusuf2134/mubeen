from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mubeen.db.base import Base

if TYPE_CHECKING:
    from mubeen.db.models.masjid import Masjid


class OperatorAccount(Base):
    """Login credential for an imam / AV volunteer, scoped to exactly one masjid."""

    __tablename__ = "operator_accounts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    masjid_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("masjids.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    masjid: Mapped[Masjid] = relationship("Masjid", back_populates="operator_accounts")
