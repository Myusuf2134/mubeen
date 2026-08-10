"""Regression test: trailing Deepgram finals flushed during close() must reach results().

Before the drain fix, DeepgramTranscriber.close() cancelled _listener immediately
after send_close_stream(). Any finals that Deepgram flushed after receiving
CloseStream were lost because the reader task was killed before it could put them
on the queue.

After the fix, close() awaits _listener (up to _DRAIN_TIMEOUT) so the reader
finishes naturally, trailing finals land in the queue, and results() yields them
before seeing EOF.

These tests verify the drain behaviour using DeepgramTranscriber with a mocked
_socket and _listener so no real Deepgram connection is required.
"""

from __future__ import annotations

import asyncio

import pytest

from mubeen.services.transcription import DeepgramTranscriber, TranscriptResult


def _make_transcriber(
    trailing: list[TranscriptResult],
    listener_delay: float = 0.05,
) -> DeepgramTranscriber:
    """Return a DeepgramTranscriber wired to a fake listener.

    The fake listener waits `listener_delay` seconds then puts `trailing`
    items followed by the sentinel — simulating Deepgram flushing finals
    after receiving CloseStream.
    """
    t = object.__new__(DeepgramTranscriber)
    t._queue = asyncio.Queue()
    t._socket = None
    t._cm = None
    t._listener = None

    async def _fake_listener() -> None:
        await asyncio.sleep(listener_delay)
        for r in trailing:
            await t._queue.put(r)
        await t._queue.put(None)  # sentinel: EOF

    t._listener = asyncio.create_task(_fake_listener())
    return t


# ── Drain correctness ─────────────────────────────────────────────────────────


async def test_trailing_final_reaches_results_after_close() -> None:
    """Trailing final flushed during close() must be yielded by results()."""
    trailing = [TranscriptResult(text="الخاتمة", is_final=True, confidence=0.98)]
    t = _make_transcriber(trailing)

    collected: list[TranscriptResult] = []

    async def _collect() -> None:
        async for r in t.results():
            collected.append(r)

    collect_task = asyncio.create_task(_collect())
    await t.close()  # drain: waits for _fake_listener to finish
    await collect_task

    assert len(collected) == 1
    assert collected[0].text == "الخاتمة"
    assert collected[0].is_final is True
    assert collected[0].confidence == pytest.approx(0.98)


async def test_multiple_trailing_finals_all_reach_results() -> None:
    trailing = [
        TranscriptResult(text="أولاً", is_final=True, confidence=0.97),
        TranscriptResult(text="ثانياً", is_final=True, confidence=0.96),
    ]
    t = _make_transcriber(trailing)

    collected: list[TranscriptResult] = []

    async def _collect() -> None:
        async for r in t.results():
            collected.append(r)

    collect_task = asyncio.create_task(_collect())
    await t.close()
    await collect_task

    assert len(collected) == 2
    assert [r.text for r in collected] == ["أولاً", "ثانياً"]


async def test_no_trailing_finals_close_returns_quickly() -> None:
    """close() with no trailing items should complete without hanging."""
    t = _make_transcriber([], listener_delay=0.01)

    collected: list[TranscriptResult] = []

    async def _collect() -> None:
        async for r in t.results():
            collected.append(r)

    collect_task = asyncio.create_task(_collect())
    await t.close()
    await collect_task

    assert collected == []


# ── Timeout / force-cancel safety ────────────────────────────────────────────


async def test_close_does_not_hang_if_listener_takes_too_long() -> None:
    """close() must be bounded: force-cancel listener if it exceeds _DRAIN_TIMEOUT."""
    t = object.__new__(DeepgramTranscriber)
    t._queue = asyncio.Queue()
    t._socket = None
    t._cm = None
    t._DRAIN_TIMEOUT = 0.1  # shorten timeout for the test

    async def _stalled_listener() -> None:
        await asyncio.sleep(999)  # never ends naturally
        await t._queue.put(None)

    t._listener = asyncio.create_task(_stalled_listener())

    # close() should return within a reasonable time (< 1 s) despite the stall.
    await asyncio.wait_for(t.close(), timeout=1.0)

    assert t._listener.done()


# ── Class attribute ───────────────────────────────────────────────────────────


def test_drain_timeout_class_attr() -> None:
    assert DeepgramTranscriber._DRAIN_TIMEOUT == 3.0
