"""Tests that per-endpoint rate limits fire and return 429.

Each test runs with a fresh limiter state (conftest reset_rate_limiter autouse
fixture calls limiter._storage.reset() before every test).

Limits under test:
  POST /api/auth/login   — 10/minute
  POST /api/auth/signup  —  5/minute
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_login_rate_limited(client: AsyncClient) -> None:
    """Exceeding 10 login attempts per minute returns 429."""
    payload = {"email": "rl-login@example.com", "password": "wrong"}
    statuses = [
        (await client.post("/api/auth/login", json=payload)).status_code
        for _ in range(11)
    ]
    assert 429 in statuses, f"expected 429 within 11 requests; got {statuses}"


async def test_signup_rate_limited(client: AsyncClient) -> None:
    """Exceeding 5 signup attempts per minute returns 429."""
    statuses = []
    for i in range(7):
        resp = await client.post(
            "/api/auth/signup",
            json={"email": f"rl-signup-{i}@example.com", "password": "Str0ng-Passw0rd!"},
        )
        statuses.append(resp.status_code)
    assert 429 in statuses, f"expected 429 within 7 requests; got {statuses}"


async def test_requests_below_limit_are_not_blocked(client: AsyncClient) -> None:
    """Requests within the per-minute window pass through normally."""
    payload = {"email": "rl-ok@example.com", "password": "wrong"}
    for _ in range(5):
        resp = await client.post("/api/auth/login", json=payload)
        assert resp.status_code != 429, "request within limit should not be blocked"
