# Caption Waterfall Auto-Scroll Fix

**Date:** 2026-08-14  
**Status:** Implemented, TypeScript verified, ready for live testing

---

## Problem

The caption container was clipping the newest caption off the bottom edge of the viewport while old captions stayed visible at the top — the opposite of correct behavior.

**Root cause:** The caption container had `overflow-y-hidden` with no auto-scroll logic. New captions were appended to the DOM, but the container never scrolled to reveal them, so new entries rendered below the visible area and were clipped.

---

## Solution

Implemented four changes to make the container scroll to always show the newest caption:

### 1. Changed Container Overflow Mode

**File:** `src/pages/DisplayPage.tsx` line 115

**Before:**
```tsx
<div className="w-full max-w-4xl h-full overflow-y-hidden">
```

**After:**
```tsx
<div
  ref={captionContainerRef}
  className="w-full max-w-4xl h-full overflow-y-auto caption-scroll-container"
>
```

Changed from `overflow-y-hidden` (clips all overflow) to `overflow-y-auto` (scrolls when needed).

### 2. Added Refs for Container and Sentinel

**File:** `src/pages/DisplayPage.tsx` lines 22-24

```tsx
// Refs for auto-scroll to newest caption
const captionContainerRef = useRef<HTMLDivElement>(null);
const sentinelRef = useRef<HTMLDivElement>(null);
```

- `captionContainerRef`: Tracks the scrollable container element
- `sentinelRef`: Tracks a sentinel (marker) element at the bottom of the caption list

### 3. Added Auto-Scroll Effect

**File:** `src/pages/DisplayPage.tsx` lines 36-41

```tsx
// Auto-scroll to newest caption whenever history or interim changes
useEffect(() => {
  if (sentinelRef.current) {
    sentinelRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }
}, [history, interim]);
```

Whenever `history` or `interim` changes (i.e., a new caption arrives), scroll the sentinel element into view at the bottom of the container. This automatically scrolls the oldest captions out of view at the top.

### 4. Added Sentinel Element

**File:** `src/pages/DisplayPage.tsx` lines 185-187

```tsx
{/* Sentinel element for auto-scroll to bottom */}
<div ref={sentinelRef} />
```

Placed at the very end of the caption list (after interim section, inside the caption wrapper). This invisible marker is what gets scrolled into view.

### 5. Hid Scrollbar Visually

**File:** `src/index.css` (appended)

```css
/* Caption container auto-scroll with hidden scrollbar */
.caption-scroll-container {
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none;  /* IE and Edge */
}

.caption-scroll-container::-webkit-scrollbar {
  display: none;  /* Chrome, Safari, and Opera */
}
```

Hides the native scrollbar visually across all browsers, while keeping the container natively scrollable for the auto-scroll logic. On a TV display, users should not see a scrollbar.

---

## Expected Behavior After Fix

1. **Newest caption always visible:** When speech finishes and a new caption arrives, it appears at or near the bottom of the visible area.

2. **Oldest captions move out of view:** As new captions arrive, older ones smoothly slide out of view at the top via the browser's native scroll.

3. **No scrollbar visible:** The container scrolls, but no scrollbar appears on screen.

4. **Smooth motion:** The `behavior: 'smooth'` option makes scrolls animate smoothly rather than snapping instantly.

---

## Visual Timeline Example

```
Before first caption:
[Waiting for khutbah to begin...]

After first caption arrives:
───────────────────
بسم الله
In the name of Allah...
───────────────────
(sentinel scrolls into view at bottom)

After second caption arrives:
───────────────────
بسم الله
In the name of Allah...
───────────────────
الحمد لله رب العالمين
All praise is due to Allah...
───────────────────
(first caption scrolls up and out of view)
(sentinel scrolls into view at bottom again)

After third caption arrives:
───────────────────
الحمد لله رب العالمين
All praise is due to Allah...
───────────────────
قُل هُوَ اللَّهُ أَحَدٌ
Say: He is Allah, the One...
───────────────────
(oldest caption completely out of view)
(newest always at bottom, visible)
```

---

## What Changed in Code

| File | Change | Impact |
|---|---|---|
| `src/pages/DisplayPage.tsx` | Added `useRef, useEffect` imports | Enable refs and auto-scroll logic |
| `src/pages/DisplayPage.tsx` | Added `captionContainerRef` and `sentinelRef` | Track container and bottom marker |
| `src/pages/DisplayPage.tsx` | Added `useEffect` for scroll-to-sentinel | Auto-scroll when captions change |
| `src/pages/DisplayPage.tsx` | Changed container `overflow-y-hidden` → `overflow-y-auto` | Allow scrolling instead of clipping |
| `src/pages/DisplayPage.tsx` | Added sentinel `<div ref={sentinelRef} />` | Scrolling target at bottom |
| `src/index.css` | Added `.caption-scroll-container` CSS | Hide scrollbar visually |

---

## What Has NOT Changed

✓ Phrase buffer logic (backend)  
✓ Interim/history management (frontend state)  
✓ Dividers and spacing (FIX 2)  
✓ Fade-in and opacity dimming of old captions  
✓ WebSocket message format  
✓ RenderPayload shape  
✓ Other pages (operator console, etc.)

---

## Verification Status

✅ **TypeScript Compilation:** Clean, 0 errors

❌ **Live Behavior:** Cannot be verified by code review or unit tests
- `scrollIntoView()` is a browser runtime API
- Scroll position is managed by the browser DOM, not testable in Jest/Vitest
- Smooth scroll animation is visual-only
- Verification requires a real sermon with live captions

---

## How to Verify Live

1. Start a live session on the operator console
2. Speak 4-5 sentences at normal pace
3. Observe the TV display:
   - ✅ First caption appears at the bottom and stays visible
   - ✅ Second caption appears below it, first caption moves up (still visible)
   - ✅ Third caption appears, second moves up, first scrolls out of view
   - ✅ Newest caption is always readable
   - ✅ No scrollbar visible on screen
   - ✅ Scroll motion is smooth, not jerky

If behavior doesn't match, likely issues:
- `scrollIntoView()` not firing → check useEffect dependency array
- Container scrolls but behavior is jerky → browser animation/scroll conflict (report to address separately)
- Scrollbar visible → CSS not applied (check browser devtools)
- Newest caption still clipped → container height issue (check calc(100vh - header - footer))

---

## Technical Notes

### Why `scrollIntoView` instead of `scrollTop`?

`scrollIntoView({ behavior: 'smooth', block: 'end' })`:
- Automatically calculates the scroll distance needed
- Handles cases where sentinel is already partially visible
- `block: 'end'` aligns the sentinel to the bottom of the viewport
- Smooth animation is built-in

Alternative (`container.scrollTop = container.scrollHeight`):
- More direct control, but requires manual scroll distance calculation
- Might conflict with `scrollIntoView` if both are used simultaneously
- Used if smooth scroll causes visual jank with other animations

### Why Hide Scrollbar Instead of `overflow-hidden`?

- `overflow-hidden` clips content that exceeds the container (the original bug)
- CSS-hidden scrollbar (`scrollbar-width: none`) keeps native scrolling active while hiding the UI element
- This is the standard TV display pattern — scroll functionality without scrollbar visuals

### Dependency Array

The `useEffect` depends on `[history, interim]`. This means it runs every time:
- A new caption is added to history
- The interim (forming) text updates

It does NOT run when captions fade (opacity changes) or when old captions are removed from the array, which is correct — we only need to scroll when new content arrives.

---

## Files Modified

```
frontend/src/pages/DisplayPage.tsx
├─ Added imports: useRef, useEffect
├─ Added refs: captionContainerRef, sentinelRef
├─ Added useEffect hook for scroll-to-bottom
├─ Updated container className: overflow-y-auto + caption-scroll-container
├─ Updated container ref: ref={captionContainerRef}
└─ Added sentinel: <div ref={sentinelRef} />

frontend/src/index.css
└─ Added: .caption-scroll-container scrollbar hiding CSS
```

---

## Rollback Instructions

If this change causes unexpected behavior:

1. Revert `overflow-y-auto` → `overflow-y-hidden` (line 115)
2. Remove refs (lines 22-24)
3. Remove useEffect hook (lines 36-41)
4. Remove ref attributes from container (line 114)
5. Remove sentinel div (lines 185-187)
6. Remove CSS from index.css
