from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
    masjid_id: UUID

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        return v


class SignupResponse(BaseModel):
    id: UUID
    email: str
    masjid_id: UUID


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: UUID
    email: str
    masjid_id: UUID
