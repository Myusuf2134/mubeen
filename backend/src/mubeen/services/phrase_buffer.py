"""Utterance-bounded phrase buffer for batching STT results (MB-014).

PhraseBuffer batches TranscriptResult events into coherent phrase-sized chunks.
Design: emit ON speech_final (case A: prompt), coalesce multiple finals via short
debounce (case B: batch), fallback to max_window for long runs without finals (case C).

Word-boundary safety: the timed fallback flush closes only at the last complete word.
No translation, GPT calls, or downstream coupling — stage-agnostic.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from pydantic import BaseModel

from mubeen.services.transcription import TranscriptResult

_log = logging.getLogger(__name__)


class PhraseSegment(BaseModel):
    """Finalized phrase emitted by PhraseBuffer."""

    text: str
    start_ts: float
    end_ts: float
    is_final: bool = True


class PhraseBuffer:
    """Batches STT results with three-case emit model.

    A. speech_final arrives → emit promptly after coalescing debounce
    B. Multiple finals in succession → merge into ONE phrase
    C. Long run without finals → flush at max_window (fallback)

    Usage:
        buffer = PhraseBuffer(
            min_window_s=2.0, max_window_s=4.0, coalesce_debounce_s=0.2
        )
        buffer.feed(transcript_result)  # non-blocking
        phrase = await buffer.output_queue.get()
    """

    def __init__(
        self,
        min_window_s: float = 2.0,
        max_window_s: float = 4.0,
        coalesce_debounce_s: float = 0.2,
    ) -> None:
        self.min_window_s = min_window_s
        self.max_window_s = max_window_s
        self.coalesce_debounce_s = coalesce_debounce_s
        self.output_queue: asyncio.Queue[PhraseSegment] = asyncio.Queue()

        self._buffer: list[str] = []
        self._buffer_start_ts: Optional[float] = None
        self._last_update_ts: Optional[float] = None
        self._seen_final_in_buffer = False  # Track if a final has arrived in current buffer
        self._debounce_task: Optional[asyncio.Task] = None  # Coalesce finals
        self._fallback_task: Optional[asyncio.Task] = None  # Long-run safety (only after first final)
        self._emit_lock = asyncio.Lock()  # Guard emit + reset as atomic critical section

    def feed(self, result: TranscriptResult) -> None:
        """Non-blocking feed of a TranscriptResult.

        Case A: speech_final → start coalescing debounce (200ms)
        Case B: Multiple finals in succession → debounce restarts, all merge
        Case C: No finals for max_window → fallback timer flushes

        Key fix: Fallback is only armed AFTER the first final is seen.
        This prevents fallback from firing during pre-speech silence or natural pauses
        between sentences. DoD #1: finals are primary boundary, fallback is safety for
        truly stalled speech, not for natural gaps.

        Always uses put_nowait() — never blocks or awaits consumer.
        """
        now = time.time()

        # Initialize buffer on first input, but DON'T start fallback yet.
        if self._buffer_start_ts is None:
            self._buffer_start_ts = now
            self._seen_final_in_buffer = False

        # Add text to buffer (preserving spaces).
        if result.text:
            if self._buffer and not result.text.startswith(" "):
                self._buffer.append(" ")
            self._buffer.append(result.text)

        self._last_update_ts = now

        # Case A/B: On final, start coalescing debounce.
        # Arm fallback on first final (speech confirmed, now monitor for stall).
        if result.is_final:
            self._seen_final_in_buffer = True

            # Arm fallback only after first final (speech started, watch for stall)
            if not self._fallback_task or self._fallback_task.done():
                self._start_fallback_timer()

            # Start debounce to coalesce consecutive finals
            self._cancel_debounce()
            self._start_debounce()
            # Don't cancel fallback — let it monitor for stalls in the next buffer

    def _cancel_debounce(self) -> None:
        """Cancel pending coalescing debounce."""
        if self._debounce_task is not None and not self._debounce_task.done():
            self._debounce_task.cancel()
            self._debounce_task = None

    def _start_debounce(self) -> None:
        """Start short debounce to coalesce consecutive finals."""
        self._debounce_task = asyncio.create_task(self._coalesce_timer())

    async def _coalesce_timer(self) -> None:
        """Wait for coalescing window, then emit (case A/B).

        For normal multi-word phrases: emit promptly after debounce (Case A/B design).
        For very short fragments (single word): hold briefly to see if more arrives.
        """
        try:
            await asyncio.sleep(self.coalesce_debounce_s)

            # Check if this is a very short phrase that might need more context.
            # Only apply targeted hold for single-word fragments, not for phrases with 2+ words.
            text = "".join(self._buffer).strip()
            word_count = len(text.split())

            if word_count < 2 and self._buffer_start_ts is not None:
                # Single-word fragment: hold briefly (500ms) to see if more speech arrives
                # before emitting this alone. This prevents single-word flushes like "آمِن"
                # while still being much faster than the full 2.0s min_window.
                # Multi-word phrases (2+ words) skip this hold and emit promptly.
                await asyncio.sleep(0.5)

            end_ts = time.time()
            await self._emit_phrase_atomic(end_ts=end_ts, on_boundary=True)
        except asyncio.CancelledError:
            pass

    def _cancel_fallback_timer(self) -> None:
        """Cancel pending fallback timer."""
        if self._fallback_task is not None and not self._fallback_task.done():
            self._fallback_task.cancel()
            self._fallback_task = None

    def _start_fallback_timer(self) -> None:
        """Start max_window fallback (case C: long runs without finals)."""
        if self._fallback_task is None or self._fallback_task.done():
            self._fallback_task = asyncio.create_task(self._fallback_timer())

    async def _fallback_timer(self) -> None:
        """Wait max_window_s, then emit if buffer is old enough (case C)."""
        try:
            await asyncio.sleep(self.max_window_s)
            # Emit only if buffer exists and has aged to max_window.
            if self._buffer_start_ts is not None:
                elapsed = time.time() - self._buffer_start_ts
                if elapsed >= self.max_window_s:
                    end_ts = time.time()
                    await self._emit_phrase_atomic(end_ts=end_ts, on_boundary=False)
        except asyncio.CancelledError:
            pass

    async def _emit_phrase_atomic(self, end_ts: float, on_boundary: bool) -> None:
        """Atomically check buffer, emit phrase, and reset (critical section).

        Lock ensures emit + reset cannot be interrupted by another timer, even if
        a future await is added inside. Prevents race condition: check-then-emit-then-reset.

        on_boundary=True: emission via coalesce debounce (finals path)
        on_boundary=False: emission via fallback timer (max_window path)
        """
        async with self._emit_lock:
            if not self._buffer:
                return

            text = "".join(self._buffer).strip()

            if not on_boundary:
                # Fallback: trim to last word, never mid-word.
                text = self._trim_to_last_word(text)
                if not text:
                    # No complete word; discard and reset.
                    self._reset_buffer()
                    return

            start_ts = self._buffer_start_ts if self._buffer_start_ts is not None else end_ts

            phrase = PhraseSegment(
                text=text,
                start_ts=start_ts,
                end_ts=end_ts,
                is_final=True,
            )

            # Log emission path for debugging over-emit issue
            emit_path = "final-emit" if on_boundary else "fallback-emit"
            _log.debug(
                f"phrase_buffer: {emit_path}",
                text_preview=text[:40],
                on_boundary=on_boundary,
            )

            # Backpressure-safe: put_nowait never blocks.
            self.output_queue.put_nowait(phrase)

            # Reset as part of critical section.
            self._reset_buffer()

    def _reset_buffer(self) -> None:
        """Clear buffer and reset state for next phrase."""
        self._buffer.clear()
        self._buffer_start_ts = None
        self._last_update_ts = None
        self._seen_final_in_buffer = False  # Reset for next buffer

    def _trim_to_last_word(self, text: str) -> str:
        """Trim to last complete word (space-delimited).

        Single word → return as-is (complete).
        Multiple words → trim at last space (exclude partial trailing word).
        """
        trimmed = text.rstrip()
        if " " not in trimmed:
            return trimmed
        last_space_idx = trimmed.rfind(" ")
        return trimmed[:last_space_idx]

    async def close(self) -> None:
        """Gracefully shut down: emit remaining buffer and cancel timers."""
        self._cancel_debounce()
        self._cancel_fallback_timer()
        if self._buffer:
            end_ts = time.time()
            await self._emit_phrase_atomic(end_ts=end_ts, on_boundary=True)
