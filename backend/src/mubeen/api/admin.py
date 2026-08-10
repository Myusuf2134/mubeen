from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import get_current_admin, get_current_operator
from mubeen.db.models.audit import make_audit_row
from mubeen.db.models.masjid import Masjid
from mubeen.db.session import get_session
from mubeen.schemas.auth import MeResponse
from mubeen.schemas.masjid import MasjidSummary

log = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me", response_model=MeResponse)
async def get_me(  # noqa: B008
    operator=Depends(get_current_operator),  # noqa: B008
) -> MeResponse:
    return MeResponse(id=operator.id, email=operator.email, masjid_id=operator.masjid_id)


@router.get("/masjids/pending", response_model=list[MasjidSummary])
async def list_pending_masjids(  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
    admin=Depends(get_current_admin),  # noqa: B008, ARG001
) -> list[MasjidSummary]:
    """Return all masjids awaiting moderation. Platform admin only."""
    rows = (
        await db.execute(
            select(Masjid)
            .where(Masjid.moderation_status == "pending")
            .order_by(Masjid.created_at)
        )
    ).scalars().all()
    return [MasjidSummary.model_validate(m) for m in rows]


@router.post("/masjids/{masjid_id}/approve", status_code=status.HTTP_200_OK)
async def approve_masjid(  # noqa: B008
    masjid_id: UUID,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    admin=Depends(get_current_admin),  # noqa: B008
) -> dict:
    """Approve a pending masjid, making it visible publicly. Platform admin only."""
    masjid = (
        await db.execute(select(Masjid).where(Masjid.id == masjid_id))
    ).scalar_one_or_none()
    if masjid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masjid not found")

    old_status = masjid.moderation_status
    masjid.moderation_status = "approved"
    db.add(make_audit_row(
        actor_operator_id=admin.id,
        masjid_id=masjid_id,
        action="approve",
        old_values={"moderation_status": old_status},
        new_values={"moderation_status": "approved"},
    ))
    await db.commit()
    log.info("masjid_approved", masjid_id=str(masjid_id), actor=str(admin.id))
    return {"id": str(masjid_id), "moderation_status": "approved"}


@router.post("/masjids/{masjid_id}/reject", status_code=status.HTTP_200_OK)
async def reject_masjid(  # noqa: B008
    masjid_id: UUID,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    admin=Depends(get_current_admin),  # noqa: B008
) -> dict:
    """Reject a masjid, hiding it publicly without soft-deleting it. Platform admin only."""
    masjid = (
        await db.execute(select(Masjid).where(Masjid.id == masjid_id))
    ).scalar_one_or_none()
    if masjid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masjid not found")

    old_status = masjid.moderation_status
    masjid.moderation_status = "rejected"
    # deleted_at is deliberately NOT touched — rejection and soft-delete are independent.
    db.add(make_audit_row(
        actor_operator_id=admin.id,
        masjid_id=masjid_id,
        action="reject",
        old_values={"moderation_status": old_status},
        new_values={"moderation_status": "rejected"},
    ))
    await db.commit()
    log.info("masjid_rejected", masjid_id=str(masjid_id), actor=str(admin.id))
    return {"id": str(masjid_id), "moderation_status": "rejected"}
