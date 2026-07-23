from fastapi import APIRouter

from mubeen.api import admin, auth, health, masjids

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(masjids.router)
router.include_router(auth.router)
router.include_router(admin.router)
