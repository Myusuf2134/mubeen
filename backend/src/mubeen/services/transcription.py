"""Transcriber interface + implementations for live Arabic STT (MB-013).

Transport-neutral streaming contract:
  - start()       open the STT connection
  - send_audio()  push audio bytes
  - results()     async generator of TranscriptResult
  - close()       tear down

CI tests inject FakeTranscriber via monkeypatching get_transcriber() at the
route-module level (mubeen.api.khutbah.get_transcriber). DeepgramTranscriber
is used in normal operation and by the opt-in integration test.

Audio format for Deepgram live streaming (MB-013/MB-014):
  - encoding: linear16 (16-bit signed PCM)
  - sample_rate: 16000 Hz (16 kHz)
  - channels: 1 (mono)
Integration tests must resample input audio to match these parameters.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel

_log = logging.getLogger(__name__)

# Deepgram nova-3 live streaming expects linear16 PCM at 16kHz mono.
# Test harness must resample all input audio to match.
DEEPGRAM_AUDIO_FORMAT = {
    "encoding": "linear16",
    "sample_rate": 16000,
    "channels": 1,
}


class TranscriptResult(BaseModel):
    text: str
    is_final: bool
    confidence: float | None = None


class Transcriber(Protocol):
    """Transport-neutral streaming STT interface."""

    async def start(self) -> None: ...
    async def send_audio(self, chunk: bytes) -> None: ...
    def results(self) -> AsyncIterator[TranscriptResult]: ...
    async def close(self) -> None: ...


class DeepgramTranscriber:
    """Live-streaming STT via Deepgram nova-3/ar (deepgram-sdk v7).

    Usage:
        t = DeepgramTranscriber()
        await t.start()
        await t.send_audio(chunk)
        async for r in t.results():
            ...
        await t.close()

    The v7 API: AsyncDeepgramClient.listen.v1.connect() returns an
    asynccontextmanager yielding AsyncV1SocketClient. We enter/exit it
    manually so send_audio() and results() can run concurrently.
    """

    _DRAIN_TIMEOUT = 3.0

    def __init__(self) -> None:
        self._queue: asyncio.Queue[TranscriptResult | None] = asyncio.Queue()
        self._socket = None
        self._cm = None
        self._listener: asyncio.Task | None = None

    async def start(self) -> None:
        from deepgram import AsyncDeepgramClient

        from mubeen.config import settings

        client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
        self._cm = client.listen.v1.connect(
            model="nova-3",
            language="ar",
            encoding=DEEPGRAM_AUDIO_FORMAT["encoding"],
            sample_rate=DEEPGRAM_AUDIO_FORMAT["sample_rate"],
            smart_format=True,
            punctuate=True,
            interim_results=True,
        )
        self._socket = await self._cm.__aenter__()
        self._listener = asyncio.create_task(self._run_listener())

    async def _run_listener(self) -> None:
        from deepgram.listen.v1.types.listen_v1results import ListenV1Results

        try:
            async for msg in self._socket:
                if not isinstance(msg, ListenV1Results):
                    continue
                if not msg.channel.alternatives:
                    continue
                alt = msg.channel.alternatives[0]
                if not alt.transcript:
                    continue
                is_final = bool(msg.is_final or msg.speech_final)
                await self._queue.put(
                    TranscriptResult(
                        text=alt.transcript,
                        is_final=is_final,
                        confidence=alt.confidence if is_final else None,
                    )
                )
        except Exception as exc:
            _log.warning("deepgram_listener_error: %s", exc)
        finally:
            await self._queue.put(None)

    async def send_audio(self, chunk: bytes) -> None:
        if self._socket is not None:
            await self._socket.send_media(chunk)

    async def results(self) -> AsyncIterator[TranscriptResult]:  # type: ignore[override]
        while True:
            item = await self._queue.get()
            if item is None:
                return
            yield item

    async def close(self) -> None:
        """Gracefully shut down the Deepgram connection.

        Sends CloseStream so Deepgram flushes any buffered finals, then waits
        up to _DRAIN_TIMEOUT seconds for _run_listener to read them and place
        the sentinel on the queue. Results() can therefore consume trailing
        finals before seeing EOF. Force-cancels the listener on timeout so
        close() is always bounded.
        """
        if self._socket is not None:
            try:
                await self._socket.send_close_stream()
            except Exception:
                pass
        if self._listener is not None:
            try:
                await asyncio.wait_for(
                    asyncio.shield(self._listener), timeout=self._DRAIN_TIMEOUT
                )
            except (TimeoutError, asyncio.CancelledError):
                self._listener.cancel()
                await asyncio.gather(self._listener, return_exceptions=True)
        if self._cm is not None:
            try:
                await self._cm.__aexit__(None, None, None)
            except Exception:
                pass


class FakeTranscriber:
    """Deterministic, no-network transcriber for CI tests.

    Constructed with a scripted list of TranscriptResults. send_audio() is a
    no-op that increments chunk_count for assertion convenience. results()
    yields the script in order with an asyncio.sleep(0) before each item so
    cooperative scheduling matches realistic behaviour.
    """

    def __init__(self, script: list[TranscriptResult]) -> None:
        self._script = list(script)
        self.chunk_count = 0
        self._started = False

    async def start(self) -> None:
        self._started = True

    async def send_audio(self, chunk: bytes) -> None:
        self.chunk_count += 1

    async def results(self) -> AsyncIterator[TranscriptResult]:  # type: ignore[override]
        for r in self._script:
            await asyncio.sleep(0)
            yield r

    async def close(self) -> None:
        pass


def get_transcriber() -> DeepgramTranscriber:
    """Factory used by the audio route.

    Tests monkeypatch this at the call site:
        monkeypatch.setattr("mubeen.api.khutbah.get_transcriber", lambda: FakeTranscriber(...))
    """
    return DeepgramTranscriber()
