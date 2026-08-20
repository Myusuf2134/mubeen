# MB-017 Caption Waterfall Redesign — Implementation Summary

**Date:** 2026-08-14  
**Status:** Ready for visual testing (state logic verified, animations not visually confirmed)

---

## What Changed

### 1. State Management (useDisplayWebSocket.ts)

**Before:**
```typescript
const [payload, setPayload] = useState<RenderPayload | null>(null);
const [interim, setInterim] = useState(false);

return {
  state,
  message,
  payload,       // Single caption, replaced on each message
  interim,       // Boolean flag
  error,
}
```

**After:**
```typescript
const [history, setHistory] = useState<RenderPayload[]>([]);     // Last N finalized messages
const [interim, setInterim] = useState<RenderPayload | null>(null); // Currently forming text

const _HISTORY_MAX_SIZE = 6;  // Tunable constant

return {
  state,
  history,       // Array of finalized captions (newest at end)
  interim,       // RenderPayload or null (not a boolean)
  error,
}
```

### 2. Message Handling Logic (useDisplayWebSocket.ts)

**Key behavioral changes:**

- **Interim messages (is_partial=true):**
  - Update `interim` state in place (replaces previous interim)
  - NEVER added to history array
  - Clears when a final message arrives

- **Final messages (is_partial=false):**
  - Append to history array
  - If history exceeds MAX_SIZE (6), drop oldest via `.shift()`
  - Clear interim state

```typescript
if (msg.is_partial) {
  // Interim: update forming text, don't add to history
  setInterim(payload);
} else {
  // Final: add to history, clear interim
  if (payload) {
    setHistory((prev) => {
      const newHistory = [...prev, payload];
      if (newHistory.length > _HISTORY_MAX_SIZE) {
        newHistory.shift();
      }
      return newHistory;
    });
  }
  setInterim(null);
}
```

### 3. UI Rendering (DisplayPage.tsx)

**Before:**
```typescript
{!payload ? (
  <div>Waiting...</div>
) : (
  <DisplayRenderer payload={payload} interim={interim} />
)}
```

**After:**
```typescript
{history.length === 0 && !interim ? (
  <div>Waiting...</div>
) : (
  <div className="space-y-6">
    {/* Scrolling history */}
    <div className="space-y-4">
      {history.map((payload, idx) => {
        const age = history.length - idx - 1;
        const isOld = age > 2;
        const opacityClass = isOld ? 'opacity-50' : 'opacity-100';

        return (
          <div key={`caption-${idx}`} className={`caption-item transition-opacity ${opacityClass}`}>
            <DisplayRenderer payload={payload} interim={false} />
          </div>
        );
      })}
    </div>

    {/* Interim line (below history) */}
    {interim && (
      <div className="border-t border-surface-bd/50 pt-4 caption-item">
        <DisplayRenderer payload={interim} interim={true} />
      </div>
    )}
  </div>
)}
```

### 4. Animations (index.css)

Added CSS animations for caption waterfall effect:

```css
@keyframes caption-fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.caption-item {
  animation: caption-fade-in 0.5s ease-out forwards;
  transition: opacity 300ms ease;
}
```

**Animation behavior:**
- New captions fade in with slight upward slide (0.5s duration)
- Older captions (3+ from newest) gradually fade to 50% opacity
- Opacity transitions are smooth (300ms)
- Newest captions stay at 100% opacity for readability

---

## Testing Results

### State Logic Tests: ✅ ALL PASSED

Created `useDisplayWebSocket.test.ts` with 7 comprehensive tests:

```
Test Files  1 passed (1)
     Tests  7 passed (7)
   Duration  300ms
```

**Tests verify:**
1. ✅ Final messages append to history
2. ✅ Multiple finals maintain order
3. ✅ History truncates when exceeding MAX_SIZE
4. ✅ Interim messages NEVER enter history
5. ✅ Interim updates in place without pushing to history
6. ✅ Interim clears when final arrives
7. ✅ Null payloads handled gracefully

### TypeScript Compilation: ✅ NO ERRORS

```bash
npx tsc --noEmit
(no output = clean)
```

### Backend Tests: No changes to backend

Backend test suite was not run (no changes made to backend for this redesign). Previous baseline: 271 passed, 14 failed (pre-existing).

---

## Files Changed

### Frontend Only (No Backend Changes)

1. **src/hooks/useDisplayWebSocket.ts**
   - Replaced `payload` state with `history: RenderPayload[]`
   - Changed `interim: boolean` to `interim: RenderPayload | null`
   - Updated `handleMessage()` callback with new history logic
   - Added `_HISTORY_MAX_SIZE = 6` constant

2. **src/pages/DisplayPage.tsx**
   - Updated hook call: `const { history, interim } = useDisplayWebSocket()`
   - Replaced single DisplayRenderer with:
     - Loop rendering history array
     - Separate interim section below history
   - Added opacity classes based on caption age

3. **src/index.css**
   - Added `caption-fade-in` keyframe animation
   - Added `.caption-item` class with animation and transition

4. **src/hooks/useDisplayWebSocket.test.ts** (NEW)
   - Pure function tests for history management logic
   - 7 test cases covering all state transitions

---

## What Is Verified (Test-Confirmed)

✅ **History array state logic:**
- Appends finals to array in correct order
- Truncates oldest when exceeding MAX_SIZE=6
- Interim messages never enter history
- Interim clears when final arrives
- Handles null payloads gracefully

✅ **TypeScript compilation:**
- No type errors
- Hook interface matches new return type
- DisplayPage correctly destructures new props
- DisplayRenderer still accepts expected props

---

## What Is NOT Verified (Code Review Only)

❌ **Visual rendering:**
- Whether the scrolling waterfall looks right on a TV screen
- Whether opacity transitions are smooth enough
- Whether the gray interim text is readable above/below finalized captions
- How it looks when history has 0, 1, 3, 6 items

❌ **Animation timing:**
- Is 0.5s fade-in duration appropriate?
- Is 300ms opacity transition too fast/slow?
- Whether the animation feels jarring or natural on a TV viewed from distance

❌ **Layout behavior:**
- How much vertical space 6 captions + interim take
- Whether oldest captions at 50% opacity are still readable
- How it looks when a caption is very long (wraps multiple lines)

❌ **Live streaming accuracy:**
- Whether history is maintained correctly during actual sermon with real audio
- Whether interim text updates feel live and responsive
- Whether latency perception improved with visible interim feedback

---

## Design Decisions & Rationale

### Why separate `interim` as a RenderPayload?

Initially interim was a boolean flag. But DisplayRenderer needs the actual text/payload to render gray "Transcribing..." text. Tracking interim as `RenderPayload | null` lets DisplayRenderer use the same render logic for both final and interim, just with `interim={true}` flag.

### Why MAX_SIZE = 6?

Tunable constant. 6 items fits on a typical 1080p TV display when viewed from 10-15 feet, without text becoming too small. Can be adjusted down to 3-4 for smaller screens or up to 8-10 for large displays. The exact value wasn't specified; 6 is a reasonable starting point.

### Why opacity-50 for items > 2 positions from newest?

Gradual fade-to-background prevents abrupt disappearance when oldest item is dropped. Items 3+ positions back fade to 50% opacity, still readable but clearly "old." This is subjective—could also be 30%, 60%, or even fade progressively per position.

### Why put interim below history?

Placement choice. Interim below makes it feel like it's "forming" toward becoming a history entry. Could also go above, but below seems more natural directionally. Not tested visually.

---

## Edge Cases & Limitations

### Empty state
When `history.length === 0 && !interim === null`, shows "Waiting for khutbah to begin..." (unchanged from original).

### Very fast speech
If multiple finals arrive rapidly and history fills up, oldest entries start disappearing (opacity fade, then removed). No issues — history management handles this.

### Very slow speech
If only 1-2 items in history, no opacity fading occurs (only oldest 3+ fade). Display will have empty space above. This is fine.

### Null payloads
Messages with `render_payload: null` are ignored (don't enter history). This shouldn't happen in practice (backend enrichment always provides render_payload for finals), but code handles it.

---

## How to Adjust

All configuration is at the top of useDisplayWebSocket.ts:

```typescript
const _HISTORY_MAX_SIZE = 6;  // Change to 3, 4, 8, etc.
```

Animation timings in index.css:

```css
@keyframes caption-fade-in {
  /* duration: change from 0.5s to 0.3s (faster) or 0.8s (slower) */
}

.caption-item {
  transition: opacity 300ms ease;  /* change 300ms to 200ms, 500ms, etc. */
}
```

Opacity threshold in DisplayPage.tsx:

```typescript
const isOld = age > 2;  // Change to > 1 (fade sooner) or > 4 (fade later)
const opacityClass = isOld ? 'opacity-50' : 'opacity-100';  // change to opacity-40, 60, etc.
```

---

## When You Test Live

1. **Functional test (does it work?):**
   - Start a session with operator mic
   - Watch for captions appearing in sequence
   - Verify new captions push older ones up
   - Check that oldest disappear after 6 entries

2. **Visual test (does it look good?):**
   - Are new captions' fade-in animation smooth?
   - Is the opacity fade of older captions visible or too subtle?
   - Does the interim gray text update visibly as you speak?
   - Does everything read clearly from across the room?

3. **Latency test (does interim help?):**
   - Speak a phrase, measure time until gray interim appears vs time until final appears
   - Is the interim appearing early enough to feel "live" while final is processing?
   - Does seeing interim text improve perceived latency even if final takes 2-3 seconds?

Report back:
- Whether scrolling/fading behavior works as expected
- Whether animation timings feel natural
- Whether any adjustments to MAX_SIZE, opacity, or animation durations are needed
- Whether interim rendering helps with latency perception

---

## No Backend Changes

This is a **frontend-only redesign**. The WebSocket message stream, PhraseBuffer, translation, and corpus matching are unchanged. DisplayRenderer component is unchanged. Only state management and rendering layout changed.
