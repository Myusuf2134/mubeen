from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends

from mubeen.api.deps import get_current_operator
from mubeen.schemas.auth import MeResponse

log = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me", response_model=MeResponse)
async def get_me(  # noqa: B008
    operator=Depends(get_current_operator),  # noqa: B008
) -> MeResponse:
    return MeResponse(id=operator.id, email=operator.email, masjid_id=operator.masjid_id)
