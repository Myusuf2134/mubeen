"""Shared FastAPI dependencies and auth helpers."""

from __future__ import annotations

import datetime
from uuid import UUID

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mubeen.config import settings
from mubeen.db.session import get_session

log = structlog.get_logger()

_bearer = HTTPBearer()
_bearer_optional = HTTPBearer(auto_error=False)

_ALGORITHM = "HS256"
_TOKEN_TTL_HOURS = 8


def create_operator_token(operator_id: UUID, masjid_id: UUID) -> str:
    """Sign a JWT scoped to one operator + masjid."""
    payload = {
        "operator_id": str(operator_id),
        "masjid_id": str(masjid_id),
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=_TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def verify_operator_for_masjid(
    credentials: HTTPAuthorizationCredentials,
    masjid_id: UUID,
) -> UUID:
    """Decode the Bearer JWT and assert it is scoped to masjid_id.

    Raises 401 for invalid/expired tokens, 403 for wrong-masjid tokens.
    Returns the operator_id from the token.
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[_ALGORITHM])
        token_masjid_id = UUID(payload["masjid_id"])
        operator_id = UUID(payload["operator_id"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        log.warning("invalid_operator_token", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if token_masjid_id != masjid_id:
        log.warning("operator_masjid_mismatch", token_masjid=token_masjid_id, requested=masjid_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token is not valid for this masjid",
        )

    return operator_id


async def get_current_operator(  # noqa: B008
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> "OperatorAccount":  # type: ignore[name-defined]  # noqa: F821
    """Resolve the Bearer JWT to an OperatorAccount row.

    Returns 401 for missing, tampered, or expired tokens.
    Imported here lazily to avoid a circular-import cycle at module load.
    """
    from mubeen.db.models.operator import OperatorAccount  # local to break cycle

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials, settings.secret_key, algorithms=[_ALGORITHM]
        )
        operator_id = UUID(payload["operator_id"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        log.warning("invalid_auth_token", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    operator = (
        await db.execute(select(OperatorAccount).where(OperatorAccount.id == operator_id))
    ).scalar_one_or_none()
    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return operator
