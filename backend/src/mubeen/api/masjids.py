from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Float, Integer, bindparam, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mubeen.api.deps import verify_operator_for_masjid
from mubeen.db.models.khutbah import KhutbahSession
from mubeen.db.models.masjid import IqamahTime, JumuahTime, Masjid
from mubeen.db.session import get_session
from mubeen.schemas.masjid import (
    AdhanTimes,
    IqamahTimeOut,
    JumuahTimeOut,
    MasjidDetail,
    MasjidSummary,
    PatchIqamahRequest,
    PatchJumuahRequest,
)
from mubeen.services.prayer_times import get_adhan_times

log = structlog.get_logger()
router = APIRouter(prefix="/masjids", tags=["masjids"])
_bearer = HTTPBearer()

# ── Helpers ─────────────────────────────────────────────────────────────────


async def _get_masjid_or_404(masjid_id: UUID, db: AsyncSession) -> Masjid:
    result = await db.execute(
        select(Masjid)
        .where(Masjid.id == masjid_id)
        .options(
            selectinload(Masjid.iqamah_times),
            selectinload(Masjid.jumuah_times),
        )
    )
    masjid = result.scalar_one_or_none()
    if masjid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masjid not found")
    return masjid


def _build_masjid_detail(
    masjid: Masjid,
    has_live: bool,
    latest_session_id: UUID | None,
) -> MasjidDetail:
    adhan = get_adhan_times(masjid.lat, masjid.lon, masjid.calculation_method)
    return MasjidDetail(
        id=masjid.id,
        name=masjid.name,
        address_line=masjid.address_line,
        city=masjid.city,
        state=masjid.state,
        country=masjid.country,
        lat=masjid.lat,
        lon=masjid.lon,
        phone=masjid.phone,
        website=masjid.website,
        calculation_method=masjid.calculation_method,
        adhan_times=AdhanTimes(**adhan),
        iqamah_times=[IqamahTimeOut.model_validate(it) for it in masjid.iqamah_times],
        jumuah_times=[JumuahTimeOut.model_validate(jt) for jt in masjid.jumuah_times],
        has_live_session=has_live,
        latest_session_id=latest_session_id,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/search", response_model=list[MasjidSummary])
async def search_masjids(  # noqa: B008
    request: Request,  # noqa: ARG001 — required by slowapi
    q: str | None = Query(None, max_length=100, description="Name search (case-insensitive)"),
    city: str | None = Query(None, max_length=100, description="City / area search"),
    lat: float | None = Query(None, ge=-90, le=90, description="Near-me: user latitude"),
    lon: float | None = Query(None, ge=-180, le=180, description="Near-me: user longitude"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[MasjidSummary]:
    """Search masjids by name, city, or proximity. Provide exactly one of: q, city, or lat+lon."""
    if lat is not None and lon is not None:
        # Near-me: Haversine distance via parameterised SQL expression.
        # bindparams with explicit types are required by asyncpg's binary protocol.
        # LEAST/GREATEST clamp prevents ASIN domain error from floating-point rounding.
        stmt = text("""
            SELECT id, name, city, state, country, lat, lon,
                6371.0 * 2 * ASIN(SQRT(LEAST(1.0, GREATEST(0.0,
                    POWER(SIN(RADIANS(lat - :lat) / 2), 2) +
                    COS(RADIANS(:lat)) * COS(RADIANS(lat)) *
                    POWER(SIN(RADIANS(lon - :lon) / 2), 2)
                )))) AS distance_km
            FROM masjids
            ORDER BY distance_km
            LIMIT :limit
        """).bindparams(
            bindparam("lat", type_=Float()),
            bindparam("lon", type_=Float()),
            bindparam("limit", type_=Integer()),
        )
        rows = (await db.execute(stmt, {"lat": lat, "lon": lon, "limit": limit})).mappings().all()
        return [MasjidSummary(**dict(r)) for r in rows]

    if q:
        stmt = (
            select(Masjid)
            .where(func.lower(Masjid.name).contains(q.lower()))
            .order_by(Masjid.name)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [MasjidSummary.model_validate(m) for m in rows]

    if city:
        stmt = (
            select(Masjid)
            .where(func.lower(Masjid.city).contains(city.lower()))
            .order_by(Masjid.name)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [MasjidSummary.model_validate(m) for m in rows]

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Provide one of: q (name search), city, or lat+lon (near-me)",
    )


@router.get("/{masjid_id}", response_model=MasjidDetail)
async def get_masjid(  # noqa: B008
    request: Request,  # noqa: ARG001
    masjid_id: UUID,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> MasjidDetail:
    masjid = await _get_masjid_or_404(masjid_id, db)

    # Check for a live session
    live_result = await db.execute(
        select(KhutbahSession.id)
        .where(KhutbahSession.masjid_id == masjid_id, KhutbahSession.status == "live")
        .limit(1)
    )
    has_live = live_result.scalar_one_or_none() is not None

    # Latest completed session for the "Summarize" button
    latest_result = await db.execute(
        select(KhutbahSession.id)
        .where(KhutbahSession.masjid_id == masjid_id, KhutbahSession.status == "completed")
        .order_by(KhutbahSession.ended_at.desc())
        .limit(1)
    )
    latest_session_id = latest_result.scalar_one_or_none()

    return _build_masjid_detail(masjid, has_live, latest_session_id)


@router.put("/{masjid_id}/iqamah", response_model=list[IqamahTimeOut])
async def update_iqamah(  # noqa: B008
    masjid_id: UUID,
    body: PatchIqamahRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> list[IqamahTimeOut]:
    """Replace all iqamah times for a masjid. Requires a Bearer token scoped to this masjid."""
    verify_operator_for_masjid(credentials, masjid_id)
    await _get_masjid_or_404(masjid_id, db)

    await db.execute(delete(IqamahTime).where(IqamahTime.masjid_id == masjid_id))
    new_rows = [
        IqamahTime(
            masjid_id=masjid_id,
            prayer=entry.prayer,
            minutes_after_adhan=entry.minutes_after_adhan,
            fixed_time=entry.fixed_time,
        )
        for entry in body.iqamah_times
    ]
    db.add_all(new_rows)
    await db.commit()
    for row in new_rows:
        await db.refresh(row)
    log.info("iqamah_updated", masjid_id=str(masjid_id), count=len(new_rows))
    return [IqamahTimeOut.model_validate(r) for r in new_rows]


@router.put("/{masjid_id}/jumuah", response_model=list[JumuahTimeOut])
async def update_jumuah(  # noqa: B008
    masjid_id: UUID,
    body: PatchJumuahRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> list[JumuahTimeOut]:
    """Replace all Jumu'ah times for a masjid. Requires a Bearer token scoped to this masjid."""
    verify_operator_for_masjid(credentials, masjid_id)
    await _get_masjid_or_404(masjid_id, db)

    await db.execute(delete(JumuahTime).where(JumuahTime.masjid_id == masjid_id))
    new_rows = [
        JumuahTime(
            masjid_id=masjid_id,
            label=entry.label,
            language=entry.language,
            time=entry.time,
            sort_order=entry.sort_order,
        )
        for entry in body.jumuah_times
    ]
    db.add_all(new_rows)
    await db.commit()
    for row in new_rows:
        await db.refresh(row)
    log.info("jumuah_updated", masjid_id=str(masjid_id), count=len(new_rows))
    return [JumuahTimeOut.model_validate(r) for r in new_rows]
