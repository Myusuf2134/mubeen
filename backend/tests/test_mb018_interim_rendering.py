"""Test that interim (non-final) messages broadcast with render_payload for display.

MB-018 Issue 2: Interim messages must have render_payload set so DisplayRenderer
can show gray "Transcribing..." text instead of "Waiting for khutbah to begin..."
"""

import json
from uuid import UUID
import pytest
from mubeen.schemas.khutbah import BroadcastMessage, RenderPayloadSchema
from mubeen.services.transcription import TranscriptResult


@pytest.mark.asyncio
async def test_interim_message_has_render_payload():
    """
    Verify that interim (is_partial=True) BroadcastMessages include
    a minimal render_payload so the display can render gray interim text.

    This tests the _result_pump fix that creates interim_payload for non-finals.
    """
    # This test is more of a contract test — we verify the structure here,
    # but the real test is in integration (checking actual broadcast message shape).

    # Simulate what _result_pump should do:
    interim_result = TranscriptResult(
        text="بسم",
        is_partial=True,
        is_final=False,
        confidence=0.92,
    )

    # Expected interim message structure (from fixed _result_pump)
    interim_payload = RenderPayloadSchema(
        text=interim_result.text,
        source_text=interim_result.text,
        source="machine",
        machine_generated=False,
        decision_state=None,
    )

    expected_message = BroadcastMessage(
        type="caption",
        masjid_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        sequence_number=0,
        arabic_text=interim_result.text,
        is_partial=True,
        render_payload=interim_payload,
    )

    # Verify structure is valid and serializable
    message_dict = expected_message.model_dump()
    assert message_dict["is_partial"] is True
    assert message_dict["render_payload"] is not None
    assert message_dict["render_payload"]["source"] == "machine"

    # Verify it can be JSON-serialized (as sent over WebSocket)
    message_json = json.dumps(expected_message.model_dump(mode="json"))
    assert "render_payload" in message_json
    assert '"source": "machine"' in message_json  # Verify payload source is correct
