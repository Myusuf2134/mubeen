from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from mubeen.db.base import Base


def make_audit_row(
    *,
    actor_operator_id: UUID | None,
    masjid_id: UUID | None,
    action: str,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> MasjidAuditLog:
    """Return an unsaved MasjidAuditLog instance. Add it to the session and commit."""
    return MasjidAuditLog(
        actor_operator_id=actor_operator_id,
        masjid_id=masjid_id,
        entity_type="masjid",
        entity_id=masjid_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
    )


class MasjidAuditLog(Base):
    __tablename__ = "masjid_audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_operator_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    masjid_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
