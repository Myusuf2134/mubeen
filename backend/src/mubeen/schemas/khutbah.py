"""Pydantic schemas for the khutbah WebSocket transport and session lifecycle."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BroadcastMessage(BaseModel):
    """What every subscriber queue holds. Frozen so no code can mutate a shared instance."""

    model_config = ConfigDict(frozen=True)

    type: str = "caption"
    masjid_id: UUID  # always set server-side from the URL path, never from the payload
    sequence_number: int
    arabic_text: str
    english_text: str | None = None
    segment_type: str = "plain_speech"
    is_partial: bool = False


class PublishFrame(BaseModel):
    """What the operator publisher sends. extra='forbid' rejects any undeclared field.

    Deliberately minimal: masjid_id, english_text, and segment_type are intentionally
    absent. With extra='forbid', a payload that tries to smuggle any of them fails
    validation and the socket closes 1008 — stricter than silently ignoring overrides.

    Message size cap: arabic_text is bounded to 2000 chars because one frame is
    replicated into every subscriber queue; an oversized frame multiplies memory
    across all watchers.
    """

    model_config = ConfigDict(extra="forbid")

    arabic_text: str = Field(min_length=1, max_length=2000)
    sequence_number: int = Field(ge=0)  # required; publisher supplies it
    is_partial: bool = False


class StartSessionResponse(BaseModel):
    session_id: UUID
    masjid_id: UUID
    status: str
    started_at: datetime.datetime


class StopSessionResponse(BaseModel):
    session_id: UUID
    status: str
    ended_at: datetime.datetime
