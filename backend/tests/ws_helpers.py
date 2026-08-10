"""Shared ASGI WebSocket test client (extracted from test_khutbah_websockets.py).

This module is the canonical location for the in-process WS test client used by
MB-011 and MB-012 tests. Import ws_connect and WebSocketDisconnect from here.
"""

from __future__ import annotations

import asyncio
import json

from mubeen.main import app


class WebSocketDisconnect(Exception):
    """Raised when the server closes the WebSocket connection."""

    def __init__(self, code: int = 1000, reason: str = "") -> None:
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket closed with code {code}")


class _WebSocketTestSession:
    """Async ASGI WebSocket client that drives the app in the same event loop.

    Speaks the ASGI websocket scope protocol directly — no HTTP upgrade, no
    separate thread — so asyncio.Queue operations in the hub are fully coherent
    with the test's event loop.
    """

    def __init__(self, url: str) -> None:
        if "?" in url:
            path, qs = url.split("?", 1)
        else:
            path, qs = url, ""
        self._path = path
        self._query_string = qs.encode()
        self._client_to_app: asyncio.Queue[dict] = asyncio.Queue()
        self._app_to_client: asyncio.Queue[dict] = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self.close_code: int | None = None

    async def __aenter__(self) -> _WebSocketTestSession:
        scope: dict = {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "headers": [],
            "path": self._path,
            "query_string": self._query_string,
            "root_path": "",
            "scheme": "ws",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }

        async def _receive() -> dict:
            return await self._client_to_app.get()

        async def _send(message: dict) -> None:
            await self._app_to_client.put(message)

        await self._client_to_app.put({"type": "websocket.connect"})
        self._task = asyncio.create_task(app(scope, _receive, _send))

        # Wait for the first app response: accept or close.
        msg = await self._app_to_client.get()
        if msg["type"] == "websocket.close":
            self.close_code = msg.get("code", 1000)
            await asyncio.gather(self._task, return_exceptions=True)
            raise WebSocketDisconnect(self.close_code, msg.get("reason", ""))
        assert msg["type"] == "websocket.accept", f"Unexpected first message: {msg!r}"
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self._task and not self._task.done():
            try:
                await self._client_to_app.put({"type": "websocket.disconnect", "code": 1000})
                await asyncio.wait_for(self._task, timeout=1.0)
            except (TimeoutError, Exception):
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)

    async def send_json(self, data: dict) -> None:
        await self._client_to_app.put({"type": "websocket.receive", "text": json.dumps(data)})

    async def send_text(self, text: str) -> None:
        await self._client_to_app.put({"type": "websocket.receive", "text": text})

    async def send_bytes(self, data: bytes) -> None:
        await self._client_to_app.put({"type": "websocket.receive", "bytes": data})

    async def receive_json(self) -> dict:
        while True:
            msg = await self._app_to_client.get()
            if msg["type"] == "websocket.send":
                return json.loads(msg.get("text", ""))
            if msg["type"] == "websocket.close":
                self.close_code = msg.get("code", 1000)
                raise WebSocketDisconnect(self.close_code, msg.get("reason", ""))


def ws_connect(url: str) -> _WebSocketTestSession:
    """Async context manager for an in-process ASGI WebSocket connection."""
    return _WebSocketTestSession(url)


def valid_frame(seq: int = 1, text: str = "بسم الله", *, is_partial: bool = False) -> dict:
    """Return a minimal valid PublishFrame payload."""
    return {"arabic_text": text, "sequence_number": seq, "is_partial": is_partial}
