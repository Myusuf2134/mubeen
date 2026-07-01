# Mawaqit Prayer-Time Approach — Research Findings

## What Mawaqit Does

Mawaqit.net is a mosque management platform serving 10,000+ mosques globally. Their core approach:

- Store each mosque's GPS coordinates and calculation method preference.
- Compute adhan (call-to-prayer) times dynamically from coordinates using a standard astronomical algorithm — never stored, always recomputed (they change daily and are deterministic).
- Let mosque admins store iqamah times as fixed values (not computed from adhan).
- Accept an annual calendar import for mosques that use a pre-printed schedule (not relevant to our use case).

## Algorithm: the `adhan` library (batoulapps)

The canonical open-source implementation used by Mawaqit and most serious prayer-time apps is [batoulapps/adhan-js](https://github.com/batoulapps/Adhan) — a high-precision port of the algorithm from Jean Meeus's *Astronomical Algorithms* (2nd ed.).

**Python equivalent:** `adhanpy` (PyPI) — a direct port of `adhan-java`, same calculation methods and precision.

## Calculation Methods We Support

| Method | Primary region |
|---|---|
| ISNA (Islamic Society of North America) | North America — our default |
| MWL (Muslim World League) | Europe, Far East |
| UMM_AL_QURA | Saudi Arabia / Mecca |
| EGYPT | Africa, Syria |
| KARACHI | Pakistan, Bangladesh |
| DUBAI | UAE |
| KUWAIT | Kuwait |
| QATAR | Qatar |
| SINGAPORE | Singapore |
| MOON_SIGHTING_COMMITTEE | North America (alternative to ISNA) |

## What We Adopt

1. **Library:** `adhanpy` for offline, no-API-key, high-precision prayer time calculation.
2. **Adhan times:** computed fresh on every request from `(lat, lon, calculation_method)`. Never persisted — they're deterministic from the inputs.
3. **Iqamah times:** stored per prayer as either:
   - `minutes_after_adhan` (offset mode), or
   - `fixed_time` (fixed clock time, takes precedence when set).
   Most North American masjids use fixed times; offset is provided for those that don't.
4. **Jumu'ah times:** variable-length list per masjid (`jumuah_times` table), each slot with optional `label` (e.g. "First Jumu'ah") and `language` BCP-47 tag (e.g. `"ar"`, `"en"`, `"so"`), ordered by `sort_order`.
5. **No external API dependency:** the directory works even when Deepgram/OpenAI are down.
