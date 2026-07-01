from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.config import settings
from mubeen.db.session import get_session

router = APIRouter()
log = structlog.get_logger()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    await db.execute(text("SELECT 1"))
    log.debug("health_check", status="ok")
    return {"status": "ok", "environment": settings.environment}
