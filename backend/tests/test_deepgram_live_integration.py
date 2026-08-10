"""Real Deepgram nova-3 streaming integration test (MB-013 opt-in gate).

NOT part of the default CI run. Execute deliberately:
    uv run pytest -m integration tests/test_deepgram_live_integration.py -v

Requires:
  - DEEPGRAM_API_KEY set in the environment (len >= 32)
  - Network access to Deepgram wss://api.deepgram.com
  - tests/khutbah.mp3 — reference khutbah audio file

Acceptance criterion: overall mean confidence of final results >= 0.95.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from mubeen.config import settings
from mubeen.services.phrase_buffer import PhraseBuffer
from mubeen.services.transcription import (
    DEEPGRAM_AUDIO_FORMAT,
    DeepgramTranscriber,
    TranscriptResult,
)

_AUDIO_FILE = Path(__file__).parent / "khutbah.mp3"
_CHUNK_SIZE = 4096  # bytes per send


@pytest.mark.integration
@pytest.mark.skipif(
    not settings.deepgram_api_key,
    reason="DEEPGRAM_API_KEY not set — skipping live integration test",
)
@pytest.mark.skipif(
    not _AUDIO_FILE.exists(),
    reason="tests/khutbah.mp3 not present — skipping live integration test",
)
async def test_deepgram_nova3_arabic_confidence() -> None:
    """Stream khutbah.mp3 through DeepgramTranscriber and assert ≥0.95 confidence."""
    transcriber = DeepgramTranscriber()
    await transcriber.start()

    audio_data = _AUDIO_FILE.read_bytes()
    finals: list[TranscriptResult] = []

    async def _feed() -> None:
        for i in range(0, len(audio_data), _CHUNK_SIZE):
            await transcriber.send_audio(audio_data[i : i + _CHUNK_SIZE])
            await asyncio.sleep(0.01)
        await transcriber.close()

    feed_task = asyncio.create_task(_feed())

    async for r in transcriber.results():
        if r.is_final and r.text:
            finals.append(r)

    await feed_task

    assert len(finals) > 0, "No final transcription results received"
    assert any(r.text for r in finals), "All finals have empty text"

    confidences = [r.confidence for r in finals if r.confidence is not None]
    assert confidences, "No confidence values returned on finals"

    mean_confidence = sum(confidences) / len(confidences)
    assert mean_confidence >= 0.95, (
        f"Mean confidence {mean_confidence:.3f} < 0.95 threshold. "
        f"Finals: {[(r.text[:30], r.confidence) for r in finals]}"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not settings.deepgram_api_key,
    reason="DEEPGRAM_API_KEY not set — skipping live integration test",
)
@pytest.mark.skipif(
    not _AUDIO_FILE.exists(),
    reason="tests/khutbah.mp3 not present — skipping live integration test",
)
async def test_phrase_buffer_call_volume_reduction() -> None:
    """Measure before/after call volume: STT finals vs. batched phrases (MB-014).

    Decodes khutbah.mp3 to PCM and streams at real-time pace through Deepgram STT
    and PhraseBuffer, counting:
    - finals: raw Deepgram final results (before batching)
    - phrases: PhraseSegment objects emitted by buffer (after batching)

    Expected: phrases < finals with meaningful coalescing (finals > 20 threshold).
    """
    # Decode MP3 and resample to Deepgram's expected format
    try:
        from pydub import AudioSegment
    except ImportError:
        pytest.skip("pydub not installed (required for MP3 decoding)")

    # Load MP3
    audio_segment = AudioSegment.from_file(_AUDIO_FILE, format="mp3")

    # Resample to match Deepgram's expected format (linear16, 16kHz, mono)
    expected_rate = DEEPGRAM_AUDIO_FORMAT["sample_rate"]  # 16000 Hz
    expected_channels = DEEPGRAM_AUDIO_FORMAT["channels"]  # 1 (mono)

    audio_segment = (
        audio_segment.set_frame_rate(expected_rate).set_channels(expected_channels)
    )

    pcm_data = audio_segment.raw_data  # 16-bit PCM bytes
    sample_rate = audio_segment.frame_rate  # Should now be 16000 Hz
    channels = audio_segment.channels  # Should now be 1

    # Calculate timing: bytes_per_second for real-time pacing
    # PCM is 16-bit (2 bytes per sample)
    bytes_per_sample = 2
    bytes_per_second = sample_rate * channels * bytes_per_sample

    transcriber = DeepgramTranscriber()
    await transcriber.start()

    buffer = PhraseBuffer(
        min_window_s=settings.phrase_buffer_min_window_seconds,
        max_window_s=settings.phrase_buffer_max_window_seconds,
        coalesce_debounce_s=settings.phrase_buffer_coalesce_debounce_seconds,
    )

    finals_count = 0
    phrases_count = 0

    async def _feed_pcm() -> None:
        """Feed PCM chunks at real-time pace (not all at once)."""
        for i in range(0, len(pcm_data), _CHUNK_SIZE):
            chunk = pcm_data[i : i + _CHUNK_SIZE]
            await transcriber.send_audio(chunk)

            # Sleep for the duration of this chunk (real-time pacing)
            chunk_duration = len(chunk) / bytes_per_second
            await asyncio.sleep(chunk_duration)

        await transcriber.close()

    feed_task = asyncio.create_task(_feed_pcm())

    # Process results while feeding.
    try:
        async for r in transcriber.results():
            buffer.feed(r)
            if r.is_final:
                finals_count += 1
    finally:
        await buffer.close()

    await feed_task

    # Drain any remaining phrases in queue.
    try:
        while True:
            buffer.output_queue.get_nowait()
            phrases_count += 1
    except asyncio.QueueEmpty:
        pass

    reduction_ratio = finals_count / phrases_count if phrases_count > 0 else 0

    # Log before/after for visibility.
    print(f"\n=== MB-014 Call Volume Measurement (khutbah.mp3) ===")
    print(f"Audio: {len(pcm_data)} bytes, {sample_rate}Hz, {channels} channels")
    print(f"Deepgram finals (before buffer):  {finals_count}")
    print(f"Phrases (after buffer):           {phrases_count}")
    if phrases_count > 0:
        print(f"Reduction ratio (finals/phrases): {reduction_ratio:.2f}x")
    print(f"Settings: coalesce={settings.phrase_buffer_coalesce_debounce_seconds}s, "
          f"min_window={settings.phrase_buffer_min_window_seconds}s, "
          f"max_window={settings.phrase_buffer_max_window_seconds}s")

    # Gate: audio must have transcribed meaningfully.
    # A full khutbah should produce many finals (e.g., multiple sentences).
    assert finals_count > 20, (
        f"Audio not transcribing properly: only {finals_count} finals from khutbah "
        f"(expected >20 for real transcription). Check PCM encoding/sample_rate."
    )

    # Phrases must not exceed finals (buffer only reduces or holds steady).
    assert phrases_count <= finals_count, (
        f"Buffer malfunction: {phrases_count} phrases > {finals_count} finals"
    )

    # Check reduction only when we have enough coalescing opportunity.
    if finals_count >= 50:
        # With 50+ finals, coalescing should achieve visible reduction.
        assert phrases_count < finals_count, (
            f"Expected reduction at {finals_count} finals: got {phrases_count} phrases "
            f"(ratio {reduction_ratio:.2f}x)"
        )
