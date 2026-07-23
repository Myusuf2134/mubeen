from __future__ import annotations

from uuid import uuid4

import bcrypt
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.api.deps import create_operator_token
from mubeen.db.models.operator import OperatorAccount
from mubeen.db.session import get_session
from mubeen.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse

log = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])

# Identical detail for wrong-password and unknown-email — prevents user enumeration.
_INVALID_DETAIL = "Invalid email or password"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _invalid_creds() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_INVALID_DETAIL,
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(  # noqa: B008
    body: SignupRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> SignupResponse:
    email = body.email.lower().strip()

    existing = (
        await db.execute(select(OperatorAccount).where(OperatorAccount.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    operator = OperatorAccount(
        id=uuid4(),
        masjid_id=body.masjid_id,
        email=email,
        hashed_password=_hash(body.password),
    )
    db.add(operator)
    await db.commit()
    log.info("operator_signup", operator_id=str(operator.id), email=email)
    return SignupResponse(id=operator.id, email=operator.email, masjid_id=operator.masjid_id)


@router.post("/login", response_model=LoginResponse)
async def login(  # noqa: B008
    body: LoginRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> LoginResponse:
    email = body.email.lower().strip()

    operator = (
        await db.execute(select(OperatorAccount).where(OperatorAccount.email == email))
    ).scalar_one_or_none()

    if operator is None or not _verify(body.password, operator.hashed_password):
        raise _invalid_creds()

    token = create_operator_token(operator.id, operator.masjid_id)
    log.info("operator_login", operator_id=str(operator.id))
    return LoginResponse(access_token=token)
