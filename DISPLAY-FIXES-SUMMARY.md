# Three Display Fixes: Latency, Layout, & Viewport — Implementation Summary

**Date:** 2026-08-14  
**Status:** Code complete, tested where testable, ready for live verification

---

## FIX 1: Revert Blanket min_window, Implement Targeted Short-Phrase Hold

### Problem
The previous fix added a blanket 2.0-second min_window wait to ALL phrases before emitting via the coalesce debounce path. This was meant to prevent single-word flushes (like "آمِن" alone with zero context) but instead added 2+ seconds of artificial latency to every phrase, including normal multi-word sentences that finalize almost immediately.

**Result:** End-to-end latency was 4-6+ seconds (unacceptable), when target is 1-2 seconds.

### Solution
**File:** `backend/src/mubeen/services/phrase_buffer.py`

Reverted the blanket min_window wait. Instead, implement a **targeted hold only for single-word fragments**:

```python
async def _coalesce_timer(self) -> None:
    """Wait for coalescing window, then emit (case A/B).
    
    For normal multi-word phrases: emit promptly after debounce.
    For very short fragments (single word): hold briefly to see if more arrives.
    """
    try:
        await asyncio.sleep(self.coalesce_debounce_s)  # 200ms debounce
        
        # Check if this is a very short phrase
        text = "".join(self._buffer).strip()
        word_count = len(text.split())
        
        if word_count < 2 and self._buffer_start_ts is not None:
            # Single-word only: hold briefly (500ms) to let more speech arrive
            # Multi-word phrases (2+ words) skip this hold and emit promptly
            await asyncio.sleep(0.5)
        
        end_ts = time.time()
        await self._emit_phrase_atomic(end_ts=end_ts, on_boundary=True)
    except asyncio.CancelledError:
        pass
```

### Behavior

| Phrase Type | Debounce | Short-word Hold | Total Latency |
|---|---|---|---|
| Single word (e.g., "آمِن") | 200ms | 500ms | ~700ms |
| 2-3 word phrase | 200ms | None | ~200ms |
| Normal multi-word | 200ms | None | ~200ms |
| Full sentence | 200ms | None | ~200ms |

### Tests Updated & Verified ✅

**test_single_word_holds_briefly_not_forever:**
- Verifies single word waits ~700ms (debounce + brief hold)
- Not the full 2.0s min_window
- ✅ PASSED

**test_multiple_words_coalesce_promptly:**
- Verifies 2-word phrase emits promptly after debounce (~200ms)
- No extra hold applied to multi-word phrases
- ✅ PASSED

**Why word_count < 2 (not < 3)?**
A 2-word phrase like "بسم الله" is already meaningful content with some context. Only genuine single-word fragments (< 2 words) get the brief hold. This balances latency against preventing bare-fragment over-emission.

### Test Results Summary (Relevant Tests)

```
tests/test_phrase_buffer_single_word.py::test_single_word_holds_briefly_not_forever  PASSED
tests/test_phrase_buffer_single_word.py::test_multiple_words_coalesce_promptly       PASSED
tests/test_mb018_interim_rendering.py::test_interim_message_has_render_payload      PASSED
                                                                    3 passed in 1.02s
```

**What has NOT been verified:**
- Live behavior during actual sermon with real audio (will test in morning)
- Whether 500ms hold is optimal for typical speech cadence
- Whether single-word-only threshold actually prevents accidental bare-word emission

---

## FIX 2: Add Visual Separators Between Caption Entries

### Problem
The waterfall of captions rendered as continuous vertical blocks without visual separation. Difficult to distinguish where one caption ends and the next begins, especially with mixed Arabic/English pairs.

### Solution
**File:** `frontend/src/pages/DisplayPage.tsx`

Added subtle horizontal divider lines above each caption entry:

```tsx
{history.map((payload, idx) => {
  const age = history.length - idx - 1;
  const isOld = age > 2;
  const opacityClass = isOld ? 'opacity-50' : 'opacity-100';

  return (
    <div key={`caption-${idx}`}>
      {/* Divider before caption */}
      <div className={`border-t border-surface-bd/30 transition-opacity ${opacityClass}`} />
      {/* Caption content */}
      <div className={`caption-item px-6 py-4 transition-opacity ${opacityClass}`}>
        <DisplayRenderer payload={payload} interim={false} masjidName="Mubeen" />
      </div>
    </div>
  );
})}
```

### Visual Result (Not Verified Live)

Expected appearance:
```
─────────────────────────────────────────
بسم الله الرحمن الرحيم
In the name of Allah, the Most Gracious, the Most Merciful.
─────────────────────────────────────────
قُل هُوَ اللَّهُ أَحَدٌ
Say, "He is Allah, the One."
─────────────────────────────────────────
(interim forming text...)
─────────────────────────────────────────
```

- Divider: `border-surface-bd/30` (low-opacity light line, matches dark theme)
- Also has padding (`px-6 py-4`) for breathing room around each entry
- Opacity transitions apply to dividers + content together (older entries fade)

### Changes Made
- Added `border-t` divider before each history entry and interim section
- Changed container from `space-y-6` to `space-y-0` (dividers provide separation)
- Added `px-6 py-4` padding to caption items for visual breathing room
- Divider opacity tracks caption opacity (older captions → fainter dividers)

### What Has NOT Been Verified
- Visual clarity on actual TV screen (low-opacity dividers might be invisible from distance)
- Whether padding amounts are appropriate for the display size
- Whether dividers help readability or look cluttered
- Whether opacity fade of dividers is noticeable/effective

---

## FIX 3: Fixed Viewport, Non-Scrolling Page

### Problem
The page grew as captions accumulated, and the browser scrollbar appeared. Operator had to scroll to see older captions. On a TV display, this is awkward and defeats the "live feed" feel.

### Solution
**File:** `frontend/src/pages/DisplayPage.tsx`

Changed page layout from `min-h-screen` scrollable to `fixed inset-0 overflow-hidden` with flexbox:

**Before:**
```tsx
<div className="min-h-screen bg-gradient-to-b ...">
  {/* Header (sticky) */}
  {/* Main content (grows with captions, page scrolls) */}
  {/* Footer */}
</div>
```

**After:**
```tsx
<div className="fixed inset-0 flex flex-col bg-gradient-to-b ... overflow-hidden">
  {/* Header (flex-shrink-0) */}
  <div className="border-b ... flex-shrink-0">...</div>
  
  {/* Main content (flex-1, contains captions) */}
  <div className="flex-1 overflow-hidden flex items-center justify-center px-6 py-8">
    <div className="w-full max-w-4xl h-full overflow-y-hidden">
      {/* Captions rendered here, overflow-hidden */}
    </div>
  </div>
  
  {/* Footer (flex-shrink-0) */}
  <div className="... flex-shrink-0">...</div>
</div>
```

### Key Changes
1. **Outer container:** `fixed inset-0 flex flex-col overflow-hidden`
   - Takes up full viewport, no scroll
   - Uses flexbox to partition space between header/content/footer

2. **Header & Footer:** `flex-shrink-0`
   - Never shrink, maintain fixed heights
   - Header stays at top, footer stays at bottom

3. **Content area:** `flex-1 overflow-hidden`
   - Takes remaining space after header/footer
   - `overflow-hidden` prevents browser scroll

4. **Caption container:** `h-full overflow-y-hidden`
   - Fixed height (full content area)
   - Captions render within this bounded region
   - New captions push old ones up, oldest fade out via opacity

### Behavior
- Page is now a fixed 100vh viewport with no scrolling
- Header + footer locked in place
- Caption waterfall lives in fixed-height middle region
- New captions appear, existing captions don't move (history array handles removal)
- Oldest captions fade via opacity + get removed from DOM when history exceeds MAX_SIZE

### What Has NOT Been Verified
- Whether the fixed layout works on different screen sizes/aspect ratios
- Whether the caption container sizing looks right (full height vs padded)
- Whether caption transitions feel smooth or jerky without CSS transform animations
- Whether the dark background properly fills the viewport on all displays
- Whether the fixed layout causes any browser rendering issues

### Technical Notes
- This implementation uses browser native scrolling prevention (overflow-hidden)
- CSS transforms or animation of individual caption positions were NOT implemented (complex in React)
- Items naturally leave the DOM when history array truncates them (max 6 items)
- Opacity transitions provide visual feedback as items fade before removal
- More sophisticated scroll/translate animations would require additional state tracking or a library

---

## Testing Results

### Backend Tests (FIX 1 — Phrase Buffer)

```
tests/test_phrase_buffer_single_word.py::test_single_word_holds_briefly_not_forever  PASSED
tests/test_phrase_buffer_single_word.py::test_multiple_words_coalesce_promptly       PASSED
tests/test_mb018_interim_rendering.py::test_interim_message_has_render_payload      PASSED

3 passed in 1.02s ✅
```

### Frontend TypeScript Compilation (FIX 2 & 3 — Display Layout)

```
npx tsc --noEmit
(no output = 0 errors) ✅
```

### Summary of Test Coverage

| Fix | Component | Test Type | Status |
|---|---|---|---|
| FIX 1 | PhraseBuffer single-word hold | Automated unit test | ✅ PASSED |
| FIX 1 | PhraseBuffer multi-word prompt | Automated unit test | ✅ PASSED |
| FIX 2 | Dividers + layout | TypeScript compilation | ✅ PASSED |
| FIX 3 | Fixed viewport | TypeScript compilation | ✅ PASSED |

**NOT Tested (Requires Live Verification):**
- FIX 1: Actual latency reduction with real audio
- FIX 2: Visual clarity and readability of dividers on TV screen
- FIX 3: Fixed viewport behavior on actual display, smooth scroll/fade transitions

---

## What Is Verified (Test-Confirmed)

✅ **FIX 1 - Phrase Buffer Logic:**
- Single-word phrases hold briefly (~500ms) but not forever (not 2.0s)
- Multi-word phrases (2+ words) emit promptly without extra hold
- Behavior matches intended design

✅ **FIX 2 & 3 - Frontend Code:**
- TypeScript compiles cleanly (0 errors)
- Code structure is syntactically correct
- Layout CSS classes are valid Tailwind utilities

---

## What Is NOT Verified (Visual/Live Testing Only)

❌ **Latency perception in live sermon:**
- Whether 700ms hold for single words actually prevents accidental bare-word emission
- Whether total end-to-end latency actually improved to 1-2s range (was 4-6s+)
- Whether operator/viewer perceives the latency improvement

❌ **FIX 2 - Visual Appearance:**
- Whether dividers are visible on actual TV screen (opacity-30 might be too faint from distance)
- Whether padding (px-6 py-4) looks right
- Whether caption blocks feel separated or still run together
- Whether older captions' faded dividers are still visible/useful

❌ **FIX 3 - Fixed Viewport Behavior:**
- Whether fixed layout works on all display sizes
- Whether captions animate smoothly as history changes (no scroll/translate animations implemented)
- Whether oldest captions fading + disappearing feels natural without explicit scroll animation
- Whether the fixed viewport causes rendering glitches or performance issues

---

## No Backend Data Format Changes

**Unmodified:**
- WebSocket message format (still BroadcastMessage with render_payload)
- RenderPayload shape (unchanged)
- Enrichment pipeline (unchanged)
- Corpus matching logic (untouched)
- Translation service (unchanged)

---

## How to Revert If Needed

**FIX 1:** Restore min_window wait in _coalesce_timer (undo the word_count < 2 check, add back time_to_min wait)
**FIX 2:** Remove border-t dividers and px-6 py-4 padding from history loop
**FIX 3:** Change `fixed inset-0 flex flex-col overflow-hidden` back to `min-h-screen`, remove `flex-1 overflow-hidden` from content area

---

## Live Testing Checklist

When you test in the morning with a live sermon:

1. **FIX 1 - Latency:**
   - Time from end of speech to caption appearing (interim gray text)
   - Compare to previous ~4-6s baseline
   - Goal: 1-2s end-to-end
   - Check: Does a single word like "آمِن" still flush alone, or does it wait for more?

2. **FIX 2 - Dividers:**
   - Are horizontal lines visible between captions?
   - Are caption blocks clearly separated?
   - Do dividers fade nicely with older captions?
   - Is padding adequate or too much?

3. **FIX 3 - Viewport:**
   - Does page scroll at all as captions accumulate?
   - Does header/footer stay fixed?
   - Do oldest captions disappear smoothly (fade + removal)?
   - Does it feel like a "live feed" now instead of a growing page?
   - Any rendering glitches or performance issues?

Report back on all three, with any adjustments needed to latency thresholds, opacity values, or container sizing.

---

## Code Locations

- **FIX 1:** `backend/src/mubeen/services/phrase_buffer.py` lines 121-138
- **FIX 1 Tests:** `backend/tests/test_phrase_buffer_single_word.py`
- **FIX 2 & 3:** `frontend/src/pages/DisplayPage.tsx` (layout refactored)
- **FIX 2 & 3 Styles:** `frontend/src/index.css` (caption animations, already in place)
