"""Test for PhraseBuffer single-word fragmentation bug (MB-018 Issue 1)."""

import asyncio
import pytest
from mubeen.services.phrase_buffer import PhraseBuffer
from mubeen.services.transcription import TranscriptResult


@pytest.mark.asyncio
async def test_single_word_holds_briefly_not_forever():
    """
    Verify the targeted single-word-flush fix.

    Scenario: A single word is received as a final, followed by a pause.

    Expected (with targeted fix): Word waits briefly (debounce 200ms + short-phrase hold 500ms)
    = ~700ms total before flushing. NOT the full min_window (2s).

    This prevents bare fragments like "آمِن" from flushing alone while keeping latency low
    for normal multi-word phrases that don't need the hold.
    """
    buffer = PhraseBuffer(
        min_window_s=2.0,
        max_window_s=4.0,
        coalesce_debounce_s=0.2,
    )

    # Feed a single word as final
    result = TranscriptResult(
        text="آمِن",
        is_partial=False,
        is_final=True,
        confidence=0.95,
    )
    buffer.feed(result)

    # Should NOT emit within debounce window (200ms)
    try:
        phrase = await asyncio.wait_for(
            buffer.output_queue.get(),
            timeout=0.3,
        )
        pytest.fail(
            f"Single word '{phrase.text}' flushed before debounce + short-phrase hold"
        )
    except asyncio.TimeoutError:
        # Correct: no phrase yet
        pass

    # Should emit after debounce (200ms) + short-phrase hold (500ms) = ~700ms
    try:
        phrase = await asyncio.wait_for(
            buffer.output_queue.get(),
            timeout=0.9,  # Wait for debounce + hold
        )
        assert phrase.text == "آمِن"
        # SUCCESS: held briefly (500ms) to see if more speech arrives, but not for 2+ seconds
    except asyncio.TimeoutError:
        pytest.fail("Word never flushed after debounce + brief hold")


@pytest.mark.asyncio
async def test_multiple_words_coalesce_promptly():
    """
    Verify that multiple finals are coalesced and emitted promptly.

    Scenario: Fast speech - word 1 (final) → word 2 (final) within 200ms,
    then pause. Should coalesce into single phrase, emitting quickly
    (just debounce window + short hold if needed).

    With the targeted fix (no blanket min_window): multi-word phrases emit
    promptly without artificial delay, just short phrases get a brief hold.
    """
    buffer = PhraseBuffer(
        min_window_s=2.0,
        max_window_s=4.0,
        coalesce_debounce_s=0.2,
    )

    # Feed first word as final
    result1 = TranscriptResult(text="بسم", is_partial=False, is_final=True, confidence=0.95)
    buffer.feed(result1)

    # Quickly feed second word as final (within 200ms debounce window)
    await asyncio.sleep(0.1)
    result2 = TranscriptResult(text="الله", is_partial=False, is_final=True, confidence=0.95)
    buffer.feed(result2)

    # With targeted fix: multi-word phrases (2+ words) skip the brief hold
    # so they emit promptly after debounce (200ms) + no extra hold
    try:
        phrase = await asyncio.wait_for(
            buffer.output_queue.get(),
            timeout=0.5,  # Debounce window + small margin
        )
        assert "بسم" in phrase.text
        assert "الله" in phrase.text
        # SUCCESS: coalesced and emitted promptly without min_window delay
    except asyncio.TimeoutError:
        pytest.fail("Multiple finals did not coalesce promptly (waited 0.5s)")
