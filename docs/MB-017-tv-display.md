# MB-017 — TV Display Client

## Overview

MB-017 implements the persistent wall-display TV client for Mubeen. It displays live khutbah captions and transcription from the WebSocket hub (MB-011) with auto-reconnect resilience, a LIVE indicator, and proper rendering of three payload states from MB-016 Stage 5.

**Route:** `GET /display/:masjidId`

**What it does:**
- Subscribes to `/api/khutbah/{masjidId}/live` WebSocket endpoint (passive subscriber, never publishes)
- Renders interim (forming) and final transcriptions with visual state machine
- Shows canonical scripture (Arabic Uthmani + Yusuf Ali) for CONFIRMED matches
- Shows machine translation with persistent "Machine translation" label for uncertain matches
- Auto-reconnects on network blips with exponential backoff (capped 32s)
- Heartbeat/liveness check (30s timeout) detects silent disconnects
- Persistent "LIVE" badge with pulse indicator when connected/reconnecting

---

## Architecture

### Frontend Components

#### `src/hooks/useDisplayWebSocket.ts`
Custom React hook managing the WebSocket lifecycle.

**Responsibilities:**
- Connect to `/api/khutbah/{masjidId}/live` via wss/ws (auto-detected)
- Parse `BroadcastMessage` from the hub: `{masjid_id, sequence_number, arabic_text, is_partial}`
- State machine: `connecting` → `connected` → `reconnecting` (on disconnect) → `disconnected` (on max retries)
- Exponential backoff: [1, 2, 4, 8, 16, 32, 32, 32, 32, 32] seconds (10 attempts)
- Heartbeat: 30-second inactivity timeout closes and triggers reconnect
- Return: `{state, message, render, error}`

**Key Methods:**
- `connect()` — establish WebSocket, auto-detect protocol (ws/wss)
- `setupHeartbeat()` — arm 30-second timeout on each message
- `handleMessage()` — parse and store `BroadcastMessage`
- Cleanup on unmount: cancel timeouts, close WebSocket

#### `src/components/DisplayRenderer.tsx`
Stateless render component for MB-016 Stage 5 payload (when integrated).

**States:**
1. **Interim (not final)** — gray/muted "forming" state
   - Original Arabic (opacity 60%)
   - Translation (opacity 50%, italicized)
   - Label: "Transcribing..." (center, xs)
   - Visual: no bold/gold treatment

2. **Final + source="scripture"** (CONFIRMED)
   - Reference card: gold surah:ayah label with vertical gold bar
   - Arabic Uthmani: prominent, gold, right-aligned (Amiri font, text-5xl)
   - Yusuf Ali translation: silver, below Arabic (text-xl)
   - Visual settle animation: fade in + blur-out on render
   - Never shows "machine translation" label

3. **Final + source="machine"** (uncertain)
   - Persistent banner: "🟢 MACHINE TRANSLATION" (mint, non-dismissible)
   - Original Arabic: gray (opacity 60%)
   - Translation: prominent English (text-3xl)
   - Visual: lower visual hierarchy than scripture

**Token usage:**
- Colors: `--text-0`, `--text-1`, `--text-2` (text ramp)
- Accents: `--gold` for scripture, `--mint` for machine labels
- Fonts: Serif (Amiri) for Arabic, Sans (Sora/Inter) for English
- Animations: `settle` (0.6s ease-out) on mount

#### `src/pages/DisplayPage.tsx`
Full-screen TV display route (`/display/:masjidId`).

**Layout:**
- **Header (sticky, top):** Masjid ID | Status indicator | Clock
- **Main content (full-height, centered):** DisplayRenderer or placeholder
- **Footer (sticky, bottom):** "Live khutbah broadcast — Do not edit"

**Status indicators (header):**
- `connected` — green pulse + "LIVE" badge
- `connecting` — gray spinner + "Connecting..."
- `reconnecting` — gold spinner + "Reconnecting..." (arms backoff countdown if visible)
- `disconnected` — red dot + "Disconnected" (after max retries)
- `error` — red pulse + "Error" + inline error message + "Auto-reconnecting in background..."

**Design:** Deep emerald field (gradient from emerald-900), dark modal bg/0-1, TV-legible type.

---

## WebSocket Transport Contract

**Endpoint:** `GET /api/khutbah/{masjidId}/live`

**No authentication required** (public display, passive subscriber).

**Message format:** `BroadcastMessage` (from MB-011)
```json
{
  "masjid_id": "uuid",
  "sequence_number": 123,
  "arabic_text": "الحمد لله رب العالمين",
  "is_partial": false
}
```

**Connection behavior:**
- Accept connection (no query param auth needed for subscriber)
- Stream all messages for the masjid_id to all connected subscribers
- On client disconnect: auto-unsubscribe
- No replay/backfill (MB-017 responsibility if needed)

---

## Running Locally

### Prerequisites
- Docker + Docker Compose (or manual Python 3.12 + Node 20+ setup)
- Mubeen repo at `/Users/moody/mubeen/`

### 1. Start Backend

```bash
cd /Users/moody/mubeen/backend

# If using Docker:
docker-compose up -d postgres redis
docker-compose up backend

# If manual:
source .venv/bin/activate
uvicorn mubeen.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on `http://localhost:8000` (or `http://192.168.x.x:8000` for LAN).

### 2. Start Frontend

```bash
cd /Users/moody/mubeen/frontend

npm install  # if needed
npm run dev
```

Frontend will run on `http://localhost:5173` (or similar Vite port).

### 3. Access Display

Navigate to: `http://localhost:5173/display/{any-uuid}`

Example:
```
http://localhost:5173/display/550e8400-e29b-41d4-a716-446655440000
```

The display page will appear and attempt to connect to the WebSocket endpoint.

---

## Manual Testing Checklist

### ✓ Connection & Reconnection

**Test 1: Initial connect**
- [ ] Open `http://localhost:5173/display/{uuid}`
- [ ] Header shows "Connecting..." spinner
- [ ] Within 1–2s, header changes to "LIVE" with green pulse
- [ ] Console: `Display: connecting to ws://...` → `Display: WebSocket connected`

**Test 2: Network blip (kill backend)**
- [ ] Display shows "LIVE" with captions flowing (if a session is active)
- [ ] Kill the backend process (or disconnect network briefly)
- [ ] Display shows "Reconnecting..." with gold spinner
- [ ] Within backoff intervals (1s, 2s, 4s…), attempts to reconnect
- [ ] Console logs: `Display: WebSocket closed` → `Display: reconnecting in Xs`

**Test 3: Heartbeat timeout**
- [ ] Open display while no captions are flowing (no messages for 30s+)
- [ ] At 30s mark, connection closes silently
- [ ] Display transitions to "Reconnecting..." state
- [ ] Auto-reconnects with backoff

**Test 4: Max reconnect exceeded**
- [ ] Keep backend down for many reconnect attempts
- [ ] After 10 attempts (with ~120s total backoff), header shows "Disconnected"
- [ ] Error banner appears: "Lost connection to live feed after multiple reconnection attempts"
- [ ] No further reconnect attempts

### ✓ Message Flow (when integrated with MB-016)

**Test 5: Interim (partial) message**
- [ ] Interim message arrives: `is_partial=true`
- [ ] Content area renders in gray, muted (opacity 60–70%)
- [ ] Label: "Transcribing..." appears
- [ ] No gold, no reverent styling

**Test 6: Final + CONFIRMED (scripture)**
- [ ] Final message with `decision_state="CONFIRMED"`, `source="scripture"`
- [ ] Content transitions smoothly: gray → gold settle animation
- [ ] Arabic Uthmani renders in gold (text-5xl, right-aligned, serif)
- [ ] Yusuf Ali translation renders beneath in silver (text-xl)
- [ ] Reference card appears: "2:255" with vertical gold bar
- [ ] NO "Machine translation" label
- [ ] Header remains "LIVE" with pulse

**Test 7: Final + MACHINE (uncertain)**
- [ ] Final message with `source="machine"`
- [ ] Content area shows "🟢 MACHINE TRANSLATION" banner (mint, uppercase)
- [ ] Banner is NOT dismissible (persistent)
- [ ] Original Arabic in gray
- [ ] Translation in prominent silver/white
- [ ] Lower visual hierarchy than scripture

### ✓ UI/UX Polish

**Test 8: Layout & readability**
- [ ] Full-screen layout (min-h-screen)
- [ ] Content centered, max-width 4xl (not TOO wide for wall TV)
- [ ] Text sizes TV-legible from 10+ feet away (text-5xl for Arabic, text-3xl for English)
- [ ] Dark background (emerald gradient) provides contrast

**Test 9: Timestamp & status**
- [ ] Header clock updates every second
- [ ] Masjid ID displayed (first 8 chars as UUID preview)
- [ ] Status indicator matches connection state

**Test 10: Footer**
- [ ] Footer text: "⧉ Live khutbah broadcast — Do not edit or interrupt"
- [ ] Stays visible, subtle (opacity 50%)

---

## Integration Points

### With MB-016 Stage 5

Currently, `DisplayPage` just renders raw `BroadcastMessage` (Arabic text only). To wire MB-016:

1. **Extract RenderPayload in backend**: When the hub publishes `BroadcastMessage`, include the MB-016 render decision payload in the broadcast schema:
   ```python
   # src/mubeen/services/broadcast.py or src/mubeen/schemas/khutbah.py
   @dataclass
   class BroadcastMessage:
       masjid_id: UUID
       sequence_number: int
       arabic_text: str          # from STT
       is_partial: bool
       render_payload: Optional[RenderPayload]  # NEW: from MB-016
       decision_state: str  # CONFIRMED | NEAR_MISS | NOT_SCRIPTURE
   ```

2. **Update publisher socket** (MB-013 audio ingest):
   ```python
   # src/mubeen/api/khutbah.py, in audio() route's _result_pump()
   # After getting Deepgram result, wire through MB-016 decision + render:
   is_scripture, render_payload = await is_scripture_with_render(normalized_text, r.text)
   message = BroadcastMessage(
       ...,
       render_payload=render_payload,
       decision_state=render_payload.decision_state if render_payload else "NOT_SCRIPTURE"
   )
   hub.publish(masjid_id, message)
   ```

3. **Update subscriber hook** (frontend):
   ```typescript
   // src/hooks/useDisplayWebSocket.ts
   const handleMessage = (event: MessageEvent) => {
     const data = JSON.parse(event.data);
     setRender(data.render_payload);  // NEW
   };
   ```

4. **Update DisplayRenderer call**:
   ```typescript
   // src/pages/DisplayPage.tsx
   <DisplayRenderer payload={render} interim={interim} masjidName={...} />
   ```

### With MB-018 (full mic→TV pipeline)

MB-017 is the display half. MB-018 will wire:
- Operator audio socket (MB-013) → Deepgram + MB-016 decision
- Session lifecycle (MB-012) start/stop triggers
- Full end-to-end test (microphone in → khutbah captions on wall TV)

---

## Monitoring & Debugging

### Frontend Console
```bash
Display: connecting to ws://localhost:8000/api/khutbah/{id}/live (attempt 1)
Display: WebSocket connected
Display: heartbeat timeout, closing WebSocket
Display: WebSocket closed
Display: reconnecting in 2s
```

### Backend Logs
```
subscriber_connected masjid_id=... subscriber_count=1
frame_published masjid_id=... sequence_number=123 subscriber_count=1
subscriber_disconnected masjid_id=... subscriber_count=0
```

### Testing Display State Transitions

**Simulate via browser DevTools Console:**

```javascript
// Manually dispatch a mock message (if hook is exposed)
// This is for testing—normally messages come from WebSocket

// In production, set breakpoints on handleMessage() in the hook
```

---

## Known Limitations & TODO

1. **No replay/backfill**: Reconnecting subscriber resumes from current moment, not from session start. Backfill is future scope (MB-017 Improvement Backlog).

2. **Single-process backend**: The in-memory broadcast hub is not shared across multiple Uvicorn workers. Until Redis pub/sub (MB-022), backend must run 1 worker, 1 Fargate replica.

3. **No MB-016 integration yet**: This PR implements the display plumbing; MB-016 payload wiring comes in a follow-up once Stage 5 is merged.

4. **Tailwind token sync**: Design tokens in `src/index.css` must stay in sync with `docs/design-reference.html`. If design changes, update both.

---

## Files Added/Modified

### Added
- `frontend/src/hooks/useDisplayWebSocket.ts` — WebSocket lifecycle hook
- `frontend/src/components/DisplayRenderer.tsx` — MB-016 payload renderer
- `frontend/src/pages/DisplayPage.tsx` — Full-screen TV display route
- `docs/MB-017-tv-display.md` — This document

### Modified
- `frontend/src/App.tsx` — Added `/display/:masjidId` route

---

## Acceptance Checklist (S7)

- [ ] Display route at `/display/:masjidId` responds with full-screen page
- [ ] WebSocket connects to `/api/khutbah/{masjidId}/live`
- [ ] Header shows "LIVE" badge (green pulse) when connected
- [ ] Header shows "Reconnecting..." when WS drops
- [ ] Auto-reconnects with exponential backoff (1, 2, 4, 8, 16, 32s)
- [ ] After 10 failed attempts, shows "Disconnected" (does not reconnect further)
- [ ] Heartbeat timeout (30s no message) triggers reconnect
- [ ] Content renders raw `BroadcastMessage.arabic_text` while awaiting MB-016 integration
- [ ] Interim messages (is_partial=true) render in gray/muted state
- [ ] No human intervention required for network blips

---

## See Also

- [MB-011 WebSocket Hub](../MB-011-brief.md)
- [MB-012 Session Lifecycle](../MB-012-brief.md)
- [MB-013 Audio Ingest](../MB-013-brief.md)
- [MB-016 Qur'an Matching](../MB-016-brief.md)
- [MB-018 End-to-End Pipeline](../MB-018-brief.md) (future)
- [Design Reference](./design-reference.html)
