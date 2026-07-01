"""Shared FastAPI dependencies and auth helpers.

JWT validation lives here. The login endpoint (which *issues* tokens) is built
in Phase 4 — for now, tokens can only be created via create_operator_token()
which is used by the Phase 4 login handler and directly by tests.
"""

from __future__ import annotations

import datetime
from uuid import UUID

import jwt
import structlog
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mubeen.config import settings

log = structlog.get_logger()

_bearer = HTTPBearer()

_ALGORITHM = "HS256"
_TOKEN_TTL_HOURS = 8


def create_operator_token(operator_id: UUID, masjid_id: UUID) -> str:
    """Sign a JWT scoped to one operator + masjid. Used by the Phase 4 login endpoint and tests."""
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
    """
    Decode the Bearer JWT and assert it is scoped to masjid_id.

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
