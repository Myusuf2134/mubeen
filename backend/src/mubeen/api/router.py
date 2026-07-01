from fastapi import APIRouter

from mubeen.api import health, masjids

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(masjids.router)
