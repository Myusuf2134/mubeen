"""Geocoding service — converts a street address to (lat, lon).

The GeocoderProtocol is the swap point: swap NominatimGeocoder for
GoogleGeocoder or MapboxGeocoder without touching any other code.
"""

from __future__ import annotations

from typing import Protocol

import httpx
import structlog

log = structlog.get_logger()


class GeocoderProtocol(Protocol):
    async def geocode(self, address: str, city: str, state: str, country: str) -> tuple[float, float]:
        """Return (lat, lon) for the given address components."""
        ...


class NominatimGeocoder:
    """Nominatim/OSM geocoder — free, no API key, max 1 req/s (fine for admin-only masjid creation)."""

    _BASE_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str = "mubeen-masjid-directory/0.1") -> None:
        self._user_agent = user_agent

    async def geocode(self, address: str, city: str, state: str, country: str) -> tuple[float, float]:
        query = f"{address}, {city}, {state}, {country}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self._BASE_URL,
                params={"q": query, "format": "json", "limit": 1, "addressdetails": 0},
                headers={"User-Agent": self._user_agent},
            )
            resp.raise_for_status()
            results = resp.json()

        if not results:
            raise ValueError(f"Geocoding returned no results for: {query!r}")

        lat, lon = float(results[0]["lat"]), float(results[0]["lon"])
        log.info("geocoded", query=query, lat=lat, lon=lon)
        return lat, lon


# Module-level default — swap by replacing this reference in tests or config
_geocoder: GeocoderProtocol = NominatimGeocoder()


async def geocode_address(address: str, city: str, state: str, country: str) -> tuple[float, float]:
    return await _geocoder.geocode(address, city, state, country)
