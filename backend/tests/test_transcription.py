"""Unit tests for the Transcriber interface (MB-013 Deliverable 1).

All tests use FakeTranscriber — no network, no API key required.
"""

from __future__ import annotations

from mubeen.services.transcription import (
    DeepgramTranscriber,
    FakeTranscriber,
    TranscriptResult,
    get_transcriber,
)

# ── FakeTranscriber behaviour ─────────────────────────────────────────────────


async def test_fake_yields_results_in_order() -> None:
    script = [
        TranscriptResult(text="بسم", is_final=False),
        TranscriptResult(text="بسم الله", is_final=True, confidence=0.99),
    ]
    t = FakeTranscriber(script)
    await t.start()

    collected = []
    async for r in t.results():
        collected.append(r)

    assert len(collected) == 2
    assert collected[0].text == "بسم"
    assert collected[0].is_final is False
    assert collected[1].text == "بسم الله"
    assert collected[1].is_final is True


async def test_fake_final_carries_confidence() -> None:
    script = [TranscriptResult(text="الحمد لله", is_final=True, confidence=0.975)]
    t = FakeTranscriber(script)
    await t.start()

    results = [r async for r in t.results()]
    assert len(results) == 1
    assert results[0].confidence == 0.975


async def test_fake_interim_has_no_confidence() -> None:
    script = [TranscriptResult(text="الحمد", is_final=False, confidence=None)]
    t = FakeTranscriber(script)
    await t.start()

    results = [r async for r in t.results()]
    assert results[0].confidence is None


async def test_fake_send_audio_records_chunk_count() -> None:
    t = FakeTranscriber([])
    await t.start()
    await t.send_audio(b"\x00" * 1024)
    await t.send_audio(b"\x00" * 512)
    assert t.chunk_count == 2


async def test_fake_empty_script_yields_nothing() -> None:
    t = FakeTranscriber([])
    await t.start()
    results = [r async for r in t.results()]
    assert results == []


async def test_fake_close_is_idempotent() -> None:
    t = FakeTranscriber([TranscriptResult(text="x", is_final=True)])
    await t.start()
    await t.close()
    await t.close()  # second close must not raise


# ── Factory ───────────────────────────────────────────────────────────────────


def test_factory_returns_deepgram_by_default() -> None:
    t = get_transcriber()
    assert isinstance(t, DeepgramTranscriber)


def test_factory_is_patchable(monkeypatch) -> None:
    fake = FakeTranscriber([])
    monkeypatch.setattr("mubeen.services.transcription.get_transcriber", lambda: fake)
    from mubeen.services import transcription

    result = transcription.get_transcriber()
    assert result is fake


# ── TranscriptResult schema ───────────────────────────────────────────────────


def test_transcript_result_defaults() -> None:
    r = TranscriptResult(text="hello", is_final=False)
    assert r.confidence is None


def test_transcript_result_with_confidence() -> None:
    r = TranscriptResult(text="hello", is_final=True, confidence=0.98)
    assert r.confidence == 0.98
