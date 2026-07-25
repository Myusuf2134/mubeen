from __future__ import annotations

import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Float, Integer, bindparam, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mubeen.api.deps import (
    get_current_operator,
    issue_scoped_token,
    verify_operator_for_masjid,
)
from mubeen.db.models.audit import MasjidAuditLog
from mubeen.db.models.khutbah import KhutbahSession
from mubeen.db.models.masjid import IqamahTime, JumuahTime, Masjid, MasjidOperatorRole
from mubeen.db.models.operator import OperatorAccount
from mubeen.db.session import get_session
from mubeen.schemas.masjid import (
    AdhanTimes,
    IqamahTimeOut,
    JumuahTimeOut,
    MasjidDetail,
    MasjidSummary,
    PatchIqamahRequest,
    PatchJumuahRequest,
    PatchMasjidRequest,
    RegisterMasjidRequest,
    RegisterMasjidResponse,
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


def _audit(
    *,
    actor_operator_id: UUID | None,
    masjid_id: UUID | None,
    action: str,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> MasjidAuditLog:
    return MasjidAuditLog(
        actor_operator_id=actor_operator_id,
        masjid_id=masjid_id,
        entity_type="masjid",
        entity_id=masjid_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", response_model=RegisterMasjidResponse, status_code=status.HTTP_201_CREATED)
async def register_masjid(  # noqa: B008
    body: RegisterMasjidRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    operator: OperatorAccount = Depends(get_current_operator),  # noqa: B008
) -> RegisterMasjidResponse:
    """Register a new masjid; the calling operator becomes owner."""
    # 409 if operator already holds any role row
    existing_role = (
        await db.execute(
            select(MasjidOperatorRole).where(MasjidOperatorRole.operator_id == operator.id)
        )
    ).scalar_one_or_none()
    if existing_role is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Operator has already registered a masjid",
        )

    # 409 on duplicate (name, city, state) among non-deleted masjids
    duplicate = (
        await db.execute(
            select(Masjid).where(
                func.lower(Masjid.name) == func.lower(body.name),
                func.lower(Masjid.city) == func.lower(body.city),
                func.lower(Masjid.state) == func.lower(body.state),
                Masjid.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A masjid with this name, city, and state already exists",
        )

    masjid = Masjid(
        name=body.name,
        address_line=body.address_line,
        city=body.city,
        state=body.state,
        country=body.country,
        lat=body.lat,
        lon=body.lon,
        calculation_method=body.calculation_method,
        phone=body.phone,
        website=body.website,
        timezone=body.timezone,
    )
    db.add(masjid)
    await db.flush()  # persist masjid so FK references resolve

    role = MasjidOperatorRole(
        masjid_id=masjid.id,
        operator_id=operator.id,
        role="owner",
    )
    db.add(role)

    operator.masjid_id = masjid.id

    db.add(_audit(
        actor_operator_id=operator.id,
        masjid_id=masjid.id,
        action="create",
        new_values={"name": masjid.name, "city": masjid.city, "state": masjid.state},
    ))
    db.add(_audit(
        actor_operator_id=operator.id,
        masjid_id=masjid.id,
        action="ownership_change",
        new_values={"operator_id": str(operator.id), "role": "owner"},
    ))

    await db.commit()
    log.info("masjid_registered", masjid_id=str(masjid.id), operator_id=str(operator.id))

    token = issue_scoped_token(operator.id, masjid.id)
    return RegisterMasjidResponse(
        id=masjid.id,
        name=masjid.name,
        city=masjid.city,
        state=masjid.state,
        access_token=token,
    )


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
        stmt = text("""
            SELECT id, name, city, state, country, lat, lon,
                6371.0 * 2 * ASIN(SQRT(LEAST(1.0, GREATEST(0.0,
                    POWER(SIN(RADIANS(lat - :lat) / 2), 2) +
                    COS(RADIANS(:lat)) * COS(RADIANS(lat)) *
                    POWER(SIN(RADIANS(lon - :lon) / 2), 2)
                )))) AS distance_km
            FROM masjids
            WHERE deleted_at IS NULL
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
            .where(
                func.lower(Masjid.name).contains(q.lower()),
                Masjid.deleted_at.is_(None),
            )
            .order_by(Masjid.name)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [MasjidSummary.model_validate(m) for m in rows]

    if city:
        stmt = (
            select(Masjid)
            .where(
                func.lower(Masjid.city).contains(city.lower()),
                Masjid.deleted_at.is_(None),
            )
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

    live_result = await db.execute(
        select(KhutbahSession.id)
        .where(KhutbahSession.masjid_id == masjid_id, KhutbahSession.status == "live")
        .limit(1)
    )
    has_live = live_result.scalar_one_or_none() is not None

    latest_result = await db.execute(
        select(KhutbahSession.id)
        .where(KhutbahSession.masjid_id == masjid_id, KhutbahSession.status == "completed")
        .order_by(KhutbahSession.ended_at.desc())
        .limit(1)
    )
    latest_session_id = latest_result.scalar_one_or_none()

    return _build_masjid_detail(masjid, has_live, latest_session_id)


@router.delete("/{masjid_id}", status_code=status.HTTP_200_OK)
async def archive_masjid(  # noqa: B008
    masjid_id: UUID,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> dict:
    """Soft-delete a masjid (set deleted_at). Requires a scoped Bearer token."""
    operator_id = verify_operator_for_masjid(credentials, masjid_id)

    result = await db.execute(select(Masjid).where(Masjid.id == masjid_id))
    masjid = result.scalar_one_or_none()
    if masjid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masjid not found")

    masjid.deleted_at = datetime.datetime.now(datetime.UTC)
    db.add(_audit(
        actor_operator_id=operator_id,
        masjid_id=masjid_id,
        action="archive",
        new_values={"deleted_at": masjid.deleted_at.isoformat()},
    ))
    await db.commit()
    log.info("masjid_archived", masjid_id=str(masjid_id))
    return {"id": str(masjid_id), "deleted": True}


@router.post("/{masjid_id}/restore", status_code=status.HTTP_200_OK)
async def restore_masjid(  # noqa: B008
    masjid_id: UUID,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> dict:
    """Restore a soft-deleted masjid (clear deleted_at). Requires a scoped Bearer token."""
    operator_id = verify_operator_for_masjid(credentials, masjid_id)

    result = await db.execute(select(Masjid).where(Masjid.id == masjid_id))
    masjid = result.scalar_one_or_none()
    if masjid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masjid not found")

    masjid.deleted_at = None
    db.add(_audit(
        actor_operator_id=operator_id,
        masjid_id=masjid_id,
        action="restore",
        old_values={"deleted_at": "was set"},
        new_values={"deleted_at": None},
    ))
    await db.commit()
    log.info("masjid_restored", masjid_id=str(masjid_id))
    return {"id": str(masjid_id), "restored": True}


@router.patch("/{masjid_id}", status_code=status.HTTP_200_OK)
async def update_masjid(  # noqa: B008
    masjid_id: UUID,
    body: PatchMasjidRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> dict:
    """Update masjid metadata. Requires a scoped Bearer token."""
    operator_id = verify_operator_for_masjid(credentials, masjid_id)

    result = await db.execute(select(Masjid).where(Masjid.id == masjid_id))
    masjid = result.scalar_one_or_none()
    if masjid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masjid not found")

    updates = body.model_dump(exclude_unset=True)
    old_values = {k: getattr(masjid, k) for k in updates}
    for k, v in updates.items():
        setattr(masjid, k, v)

    db.add(_audit(
        actor_operator_id=operator_id,
        masjid_id=masjid_id,
        action="update",
        old_values=old_values,
        new_values=updates,
    ))
    await db.commit()
    log.info("masjid_updated", masjid_id=str(masjid_id), fields=list(updates.keys()))
    return {"id": str(masjid_id), "updated": True}


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
