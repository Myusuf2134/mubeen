"""Phase 2 tests: masjid search, detail, iqamah/jumu'ah editing, and permission rejection."""

from __future__ import annotations

from uuid import uuid4

from httpx import AsyncClient

from mubeen.db.models.masjid import Masjid
from mubeen.db.models.operator import OperatorAccount

# ── Search ────────────────────────────────────────────────────────────────────


async def test_search_by_name(client: AsyncClient, seed_masjid: Masjid) -> None:
    resp = await client.get("/api/masjids/search", params={"q": "noor"})
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Masjid Al-Noor" in names


async def test_search_by_city(client: AsyncClient, seed_masjid: Masjid) -> None:
    resp = await client.get("/api/masjids/search", params={"city": "minneapolis"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_search_near_me(client: AsyncClient, seed_masjid: Masjid) -> None:
    resp = await client.get(
        "/api/masjids/search",
        params={"lat": 44.9778, "lon": -93.2650},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    # Nearest result should have a distance close to 0
    assert data[0]["distance_km"] < 1.0


async def test_search_requires_param(client: AsyncClient) -> None:
    resp = await client.get("/api/masjids/search")
    assert resp.status_code == 422


async def test_search_name_limit(client: AsyncClient, seed_masjid: Masjid) -> None:
    resp = await client.get("/api/masjids/search", params={"q": "noor", "limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) <= 1


async def test_search_near_me_requires_both_coords(client: AsyncClient) -> None:
    resp = await client.get("/api/masjids/search", params={"lat": 44.9778})
    # lon missing → falls through to no-param 422
    assert resp.status_code == 422


# ── Masjid detail ─────────────────────────────────────────────────────────────


async def test_get_masjid_detail(client: AsyncClient, seed_masjid: Masjid) -> None:
    resp = await client.get(f"/api/masjids/{seed_masjid.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(seed_masjid.id)
    assert data["name"] == "Masjid Al-Noor"
    # Prayer times are computed
    assert "fajr" in data["adhan_times"]
    assert data["has_live_session"] is False
    assert data["latest_session_id"] is None


async def test_get_masjid_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/api/masjids/{uuid4()}")
    assert resp.status_code == 404


# ── Iqamah editing ────────────────────────────────────────────────────────────


async def test_update_iqamah_with_fixed_time(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    _, token = seed_operator
    payload = {
        "iqamah_times": [
            {"prayer": "fajr", "fixed_time": "05:15:00"},
            {"prayer": "dhuhr", "minutes_after_adhan": 10},
        ]
    }
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/iqamah",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    fajr = next(r for r in rows if r["prayer"] == "fajr")
    assert fajr["fixed_time"] == "05:15:00"
    dhuhr = next(r for r in rows if r["prayer"] == "dhuhr")
    assert dhuhr["minutes_after_adhan"] == 10


async def test_update_iqamah_requires_auth(client: AsyncClient, seed_masjid: Masjid) -> None:
    payload = {"iqamah_times": [{"prayer": "fajr", "fixed_time": "05:15:00"}]}
    resp = await client.put(f"/api/masjids/{seed_masjid.id}/iqamah", json=payload)
    assert resp.status_code == 401  # missing Authorization header → 401 Unauthorized


async def test_update_iqamah_wrong_masjid_token(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    from mubeen.api.deps import create_operator_token

    wrong_token = create_operator_token(seed_operator[0].id, uuid4())  # wrong masjid
    payload = {"iqamah_times": [{"prayer": "fajr", "fixed_time": "05:15:00"}]}
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/iqamah",
        json=payload,
        headers={"Authorization": f"Bearer {wrong_token}"},
    )
    assert resp.status_code == 403


async def test_update_iqamah_invalid_token(client: AsyncClient, seed_masjid: Masjid) -> None:
    payload = {"iqamah_times": [{"prayer": "fajr", "fixed_time": "05:15:00"}]}
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/iqamah",
        json=payload,
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert resp.status_code == 401


async def test_update_iqamah_rejects_unknown_fields(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    _, token = seed_operator
    payload = {
        "iqamah_times": [{"prayer": "fajr", "fixed_time": "05:15:00"}],
        "injected_field": "evil",
    }
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/iqamah",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_update_iqamah_requires_one_time_field(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    _, token = seed_operator
    # Neither fixed_time nor minutes_after_adhan set
    payload = {"iqamah_times": [{"prayer": "fajr"}]}
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/iqamah",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ── Jumu'ah editing ───────────────────────────────────────────────────────────


async def test_update_jumuah(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    _, token = seed_operator
    payload = {
        "jumuah_times": [
            {"time": "13:00:00", "label": "First Jumu'ah", "language": "en", "sort_order": 0},
            {"time": "14:30:00", "label": "الجمعة الثانية", "language": "ar", "sort_order": 1},
        ]
    }
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/jumuah",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    assert rows[0]["label"] == "First Jumu'ah"
    assert rows[1]["language"] == "ar"


async def test_update_jumuah_replaces_previous(
    client: AsyncClient,
    seed_masjid: Masjid,
    seed_operator: tuple[OperatorAccount, str],
) -> None:
    _, token = seed_operator
    headers = {"Authorization": f"Bearer {token}"}

    # First write: 2 slots
    await client.put(
        f"/api/masjids/{seed_masjid.id}/jumuah",
        json={"jumuah_times": [{"time": "13:00:00"}, {"time": "14:30:00"}]},
        headers=headers,
    )
    # Second write: 1 slot — should replace, not append
    resp = await client.put(
        f"/api/masjids/{seed_masjid.id}/jumuah",
        json={"jumuah_times": [{"time": "13:30:00"}]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_update_jumuah_requires_auth(client: AsyncClient, seed_masjid: Masjid) -> None:
    payload = {"jumuah_times": [{"time": "13:00:00"}]}
    resp = await client.put(f"/api/masjids/{seed_masjid.id}/jumuah", json=payload)
    assert resp.status_code == 401  # missing Authorization header → 401 Unauthorized
