# Mubeen — Full Functional Specification

> This is the blueprint for how Mubeen functions. No code, just behavior.
> Build from this. At the end of each phase, work stops and nothing proceeds
> until the build is verified.

## 1. What it is

A single web app (one website, one codebase, one deployment) with two jobs:

- **A masjid prayer-times directory** — anyone can search for a masjid, see its prayer times, and view its page. No login required.
- **Live khutbah captioning** — during a khutbah, the imam's Arabic speech is transcribed and translated to English in real time, and shown as live captions on the masjid's TV screen and on the phones of anyone watching that masjid's page.

It's installable as an app on a phone (PWA), works offline for browsing the directory, and is built to a production quality bar (security, tests, accessibility), not as a prototype.

## 2. Who uses it (roles)

- **Public visitor** — no account. Searches the directory, views masjids and prayer times, watches a live khutbah, reads/summarizes a past khutbah, saves favorite masjids. Everything a visitor does is read-only.
- **Imam / masjid operator** — has a login. This is the only role that signs in. They can edit their masjid's iqamah and Jumu'ah times, and they can start/stop a live khutbah caption session for their masjid.

There are no end-user accounts. Favorites live on the visitor's own device.

> **Note on who operates a live session:** in practice the person tapping
> "Start Khutbah" is usually an AV volunteer, not the imam himself (the imam is
> at the minbar and can't hold a phone mid-khutbah). Design the start flow for a
> non-technical volunteer: one big obvious button, clear live status, minimal steps.

## 3. The pages

| Page | Who | What it does |
|---|---|---|
| Directory / Search | Public | Find a masjid three ways: by name, by "near me" (uses phone GPS, sorts by distance), or by city/area. |
| Masjid page | Public | Shows the masjid's info, full prayer times (adhan + iqamah + Jumu'ah). If a khutbah is live, a "Watch Live" button appears. After a khutbah ends, a "Summarize with AI" button appears for the saved khutbah. |
| Watch / TV display | Public | The live captions, shown as a waterfall: newest words appear at the bottom and rise upward as new lines come in. Two modes: phone view (on the masjid page) and full-screen TV view (huge text, high contrast, readable across a room). |
| Imam dashboard | Login required | Edit iqamah/Jumu'ah times; press "Start Khutbah" to begin captioning and "End Khutbah" to stop and save. |

## 4. Prayer times

We will first research how Mawaqit handles prayer times (reading their public code over the web) and write up findings before finalizing the design — so we follow a proven model.

- Adhan (call to prayer) times are computed from the masjid's location and a calculation method (e.g., ISNA, MWL, Umm al-Qura).
- Iqamah times (when the congregation actually prays, usually a few minutes after adhan) and Jumu'ah times (Friday, sometimes multiple slots) are editable by the imam, because these vary per masjid and aren't astronomical.
- Each masjid stores a location (from its street address, converted to map coordinates) so "near me" search works.

## 5. The live captioning flow — step by step

1. The masjid's microphone (wired into the masjid speakers) is connected to a phone or tablet. The operator (an AV volunteer) opens the imam dashboard and logs in.
2. They press "Start Khutbah." The app confirms broadcasting is allowed for that specific masjid and opens a secure live audio connection to our server.
3. The audio streams to Deepgram (speech-to-text, Arabic, streaming). Deepgram returns words as the imam speaks — first rough "partial" guesses, then corrected "final" versions.
4. Each finalized Arabic segment goes through a Qur'an/hadith check (see section 6) and then, if it's normal speech, through GPT-4o for English translation.
5. The Arabic + English captions are broadcast to everyone watching that masjid — the TV screen and any phones on that masjid's live page — keyed by the masjid's ID. Two masjids running khutbahs at the same time never mix, because every caption is tagged with its masjid's ID and only goes to that masjid's watchers.
6. Captions appear as a low-latency waterfall, rising from the bottom of the screen.
7. When the operator presses "End Khutbah," the session closes and the entire khutbah (Arabic + English) is saved.
8. Afterward, any visitor on that masjid's page can press "Summarize with AI" to get an AI-generated summary of the saved khutbah.

If something hiccups, the screen never freezes:

- If translation lags or fails, we show the Arabic text rather than a blank/frozen screen.
- If Deepgram drops or there's silence, the session keeps running and recovers — no server restart needed.
- If the TV's internet drops, it automatically reconnects and resumes on its own.

## 6. Qur'an & hadith handling (important — accuracy rule)

The AI will never translate Qur'an or hadith. When the imam recites:

- **Qur'an:** the system recognizes the verse by matching it against a complete copy of the Qur'an, then displays the official trusted translation you provide, plus the reference (e.g., "Qur'an 2:255"). The AI does not interpret it.
- **Hadith:** the system matches against a trusted hadith dataset you provide and displays that source's translation plus its reference/grading. The AI does not interpret it.

Only ordinary speech (the imam's own words, not scripture) is translated by GPT-4o.

> **Versioning decision:** Qur'an recognition ships first and must be rock-solid.
> **Hadith matching is v2** — it is inherently harder (many narrations, variant
> wordings, grading) and is built on top of solid Qur'an recognition, not at the
> same time. Until hadith matching is in, suspected hadith that isn't confidently
> matched falls through to showing the Arabic untranslated rather than risking a
> wrong attribution. In no case does the AI invent a translation of scripture.

You will provide the trusted sources (which Qur'an translation edition, which hadith collection). We will confirm we're legally allowed to use them (translation licensing) before shipping.

## 7. Favorites

- A visitor can save up to 5 favorite masjids (a hard limit).
- Favorites are stored on the visitor's own device — no account, no login.

## 8. Khutbah archive & AI summary

- Every completed khutbah is saved (Arabic transcript + English translation + recognized Qur'an/hadith references).
- Visitors can request an AI summary of a saved khutbah from the masjid's page.

## 9. Security (non-negotiable, built in from the start)

- **No secrets in the code.** All API keys (Deepgram, OpenAI, database) come from environment variables. We ship an `.env.example` with only placeholder names.
- **Only the imam/operator can broadcast.** Starting a khutbah and sending captions for a masjid requires a valid login token tied to that exact masjid ID. A random person cannot inject captions onto a masjid's screen. Watching is public and read-only.
- **All inputs validated.** Every request is checked against strict rules; unexpected/unknown fields are rejected.
- **Safe database access only** — parameterized queries, never hand-built SQL (prevents injection attacks).
- **Rate limiting** on public and login endpoints (prevents abuse/brute-force).
- **CORS locked** to known site addresses, not open to everyone.
- **Security headers** (CSP, HSTS, X-Frame-Options, etc.) on every response.
- **No internal errors leaked to users** — visitors see a generic message; full details are logged privately on the server.
- **Dependencies pinned,** and we flag any package with a known security issue (CVE).

## 10. Quality bar

- Full type checking (Python type hints; TypeScript in strict mode on the frontend).
- Linting + formatting configured and committed (ruff + black for Python, eslint + prettier for the frontend).
- Automated tests covering the critical paths: login, input validation, the "only the right operator can broadcast" rule, and the live-connection connect/disconnect behavior.
- Structured logging (proper logs, not stray prints).
- Health-check endpoint so we can monitor that the server is up.
- README with architecture overview, local setup, the list of environment variables, how to run tests, and how to deploy.
- Clean structure — separate folders for routes, business logic, database models, and request/response shapes. Not one giant file.
- Accessibility on the directory: keyboard navigation, alt text, semantic HTML, sufficient color contrast.
- TV captions legible across a room: large type, high contrast.
- Arabic right-to-left rendering handled correctly, with proper fonts for both Arabic and English.
- PWA done properly: installable, has an app manifest and service worker, and the directory works offline.

## 11. Technology

- **Backend:** FastAPI (Python 3.12, managed with uv), WebSockets for live captions.
- **Speech-to-text:** Deepgram, model **nova-3**, Arabic, streaming. (Validated: nova-3 transcribed a real khutbah at 0.995 confidence including dense hadith. Note: Deepgram serves Arabic on nova-3 only — nova-2 does not support Arabic.)
- **Translation:** OpenAI GPT-4o (ordinary speech only).
- **Frontend:** React (TypeScript) Progressive Web App, with Tailwind and shadcn/ui components.
- **Database:** Postgres, accessed via SQLAlchemy, with Alembic for safe, reversible database migrations.
- **Live delivery:** a WebSocket "hub" that routes each masjid's captions only to that masjid's watchers, keyed by masjid ID.

## 12. How the pieces fit together

```
Operator's phone/tablet (mic) ──audio──▶ FastAPI backend ──▶ Deepgram (Arabic speech→text, nova-3)
                                              │
                                              ▼
                                  Qur'an/Hadith matcher ──▶ trusted source translation
                                              │ (only plain speech)
                                              ▼
                                         GPT-4o translation
                                              │
                                              ▼
                             WebSocket hub (keyed by masjid ID)
                                │                         │
                                ▼                         ▼
                          Masjid TV screen        Visitors' phones

Postgres stores: masjids, prayer times, operator accounts,
saved khutbah transcripts/translations.
```

Everything is one website served from one address, with the backend and frontend together, which also keeps security simpler.

## 13. Deployment

- **Local development:** Docker (one command starts the app and database together).
- **Production:** Fly.io (handles always-on live connections well, includes managed Postgres, low cost). The website and the API are served from the same address.

## 14. Build plan (phased, with stop-and-verify gates)

1. **Foundations + Mawaqit research** — study Mawaqit's approach, then scaffold the project, config, tooling, logging, health check, and the database schema (masjids, operator accounts, prayer times with editable iqamah + Jumu'ah, khutbah sessions, saved transcripts).
2. **Directory backend + API** — search (name/near-me/city), masjid detail, prayer-time editing, rate limiting, CORS, security headers, safe errors, tests.
3. **Website frontend** — directory, masjid pages, prayer times, favorites (max 5), accessibility, PWA.
4. **Operator login + start-session** — secure login, broadcast-permission rule, tests.
5. **Live captions backend** — audio → Deepgram → Qur'an matcher → GPT-4o → broadcast by masjid ID; save the khutbah; handle drops/silence/reconnects.
6. **Caption display** — the waterfall UI for TV and phones; RTL + fonts; auto-reconnect/resume.
7. **Khutbah archive + AI summarize.**
8. **Security hardening audit.**
9. **Tests, README, deploy.**
10. **(v2) Hadith matching** — added on top of solid Qur'an recognition.

At the end of each phase, work stops, you're told exactly what to run to confirm it works, and nothing proceeds until you approve.

## 15. Still needed from the founder (not blocking the early phases)

- The trusted Qur'an translation edition and hadith collection/translation to use (with a source we're licensed to ship). Needed by Phase 5 (Qur'an) / v2 (hadith); everything before that can proceed now.
- Confirmation of at least one committed Minnesota masjid for the pilot.

---

### Validation status (as of project start)

The single biggest technical risk — whether Deepgram can transcribe real khutbah
Arabic including recited scripture — has been **tested and cleared**: nova-3
returned 0.995 overall confidence on a real ~2.5-minute khutbah dense with hadith,
with only 1 of 178 words below 0.60 confidence (a transition word, not scripture).
The speech-to-text half of the pipeline is proven. Build proceeds on tested ground.
