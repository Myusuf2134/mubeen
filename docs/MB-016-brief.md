# MB-016 — Qur'an Corpus Matching (Claude Code brief)

**Priority:** P0 · **Doctrinal.** This ticket decides whether an imam trusts Mubeen.
The governing rule overrides everything else in this brief:

> **NEVER render model output (or any uncertain match) as canonical scripture.**
> When in doubt, fall through to machine translation. A missed match costs a nicer
> render; a false match costs the product's credibility. Design for that asymmetry.

Do NOT weaken any threshold, length floor, or margin check to make a test pass. If a
test fails, fix the mechanism or tell me the threshold needs tuning against real data —
never loosen a guard to go green. (This is a hard requirement, not a preference.)

Build in the ordered STAGES below. Each stage has its own acceptance check. Do not
proceed to the next stage until the current one's check passes. Report the result of
each stage's check before moving on.

---

## STAGE 1 — Corpus ingestion (canonical, unchanged)

- Source Arabic from the **Tanzil Uthmani** distribution (v1.1) and the **Yusuf Ali**
  translation, aya-aligned, both from Tanzil so indexing matches (surah:ayah).
- Store BOTH **byte-for-byte unchanged**. The Tanzil license requires verbatim text +
  attribution ("Tanzil Project", link to tanzil.net). Persist attribution in the repo.
- Data model: a canonical table/store keyed by `(surah, ayah)` →
  `{arabic_uthmani, yusuf_ali_en, surah_name, ref_label}`. 6,236 ayat.
- This canonical copy is what gets RENDERED. It is never mutated, never normalized.

**Acceptance check S1:** all 6,236 ayat load; spot-check 3 known ayat (e.g. 1:1, 2:255,
94:6) render exact Uthmani + Yusuf Ali + correct ref label. Attribution present.

---

## STAGE 2 — Normalization (derived copy only)

- One shared `normalize_arabic(text) -> str` function. It runs on BOTH the corpus (to
  build the index) AND incoming STT (at match time). Single implementation, no duplication.
- Strips: all harakat/tanwin/shadda/sukun, tatweel + superscript alif, Quranic pause &
  ayah-end marks; normalizes alif forms (أإآ→ا), ة→ه, ى→ي, hamza-carriers; collapses whitespace.
- Build a SECOND, normalized index copy of the corpus from this function. Canonical copy
  stays untouched. The `(surah,ayah)` key bridges them: match on normalized, render from canonical.

**Acceptance check S2:** `normalize_arabic` is idempotent; unit-tested against ~10 known
(raw → normalized) pairs; the same function is demonstrably called in both the index
builder and the matcher (not two copies).

---

## STAGE 3 — Matching engine

- **Index:** inverted / n-gram index over the normalized corpus (3–4 normalized-word
  grams → candidate `(surah,ayah)` list). Goal: window → handful of candidates without
  scanning all 6,236 each call.
- **Window:** maintain a rolling buffer of the last ~15–20 normalized STT tokens. On each
  new finalized phrase (from the MB-014 PhraseBuffer), query candidates overlapping the window.
- **Score:** per candidate, a token-level sequence similarity in [0,1] (normalized
  Levenshtein ratio / token-sequence ratio) between window and the candidate's normalized text.
  Matched span must be **contiguous and in-order** within the ayah (no bag-of-words).

**Acceptance check S3:** given a normalized window equal to a known ayah's text, that ayah
is the top candidate with score ~1.0; given random non-Qur'an Arabic, top score is low.

---

## STAGE 4 — Decision: three states + guards (THE DOCTRINAL CORE)

Return one of three states. Default is NOT_SCRIPTURE — a state is only escalated when its
guards pass.

- **CONFIRMED** — ALL of: score ≥ `confirm_threshold` (start high, e.g. 0.85, in settings);
  matched run ≥ `min_match_words` (e.g. 6, in settings); best-vs-second-best margin ≥
  `min_margin` (in settings); contiguous in-order match.
- **NEAR_MISS** — cleared `min_match_words` and contiguity, but score is in
  [`nearmiss_floor`, `confirm_threshold`) OR margin is thin. Does NOT render as scripture.
- **NOT_SCRIPTURE** — below `nearmiss_floor`.

All thresholds live in settings, not literals. `is_scripture(text)` (the MB-015 seam)
returns True ONLY for CONFIRMED.

**Acceptance check S4:** thresholds are settings-driven; a CONFIRMED case renders scripture;
a NEAR_MISS case does NOT set source=scripture; changing the threshold in settings changes
the outcome (proves it's not hardcoded).

---

## STAGE 5 — Render contract + wiring

| State | Display | source | machine_generated | Logged |
|---|---|---|---|---|
| CONFIRMED | canonical Uthmani + Yusuf Ali + ref | `scripture` | `False` | yes |
| NEAR_MISS | machine translation (MB-015) | `machine` | `True` | **yes, flagged** |
| NOT_SCRIPTURE | machine translation (MB-015) | `machine` | `True` | no |

- CONFIRMED renders ONLY canonical text — never GPT output.
- NEAR_MISS logs `{window, best_candidate_ref, score, margin}` for threshold review.
- Wire into the existing flow behind the MB-015 `is_scripture()` seam; MB-015 code unchanged.

**Acceptance check S5:** end-to-end on a phrase that is a known ayah → canonical render,
source=scripture, machine_generated=False. On ordinary speech → machine path. Near-miss
produces a log entry AND a machine-translation render (not scripture).

---

## STAGE 6 — Verification sets (the proof)

- **Must-match:** known ayat (incl. recitation from the reference khutbah). All CONFIRMED.
- **Must-NOT-match (critical):** ordinary khutbah Arabic; common phrases that appear
  INSIDE ayat but shouldn't trigger alone (الحمد لله، سبحان الله، بسم الله، يا أيها الذين آمنوا);
  near-miss paraphrases. ALL must return NOT_SCRIPTURE or NEAR_MISS — **never CONFIRMED.**
- A test that asserts: no item in the must-NOT set is ever CONFIRMED. This is the doctrinal gate.

**Acceptance check S6:** must-match set all CONFIRMED; must-NOT set has ZERO CONFIRMED
(near-miss is acceptable, scripture-claim is not). Print the near-miss log for review.

---

## Config (settings, not literals)
`quran_confirm_threshold=0.85`, `quran_nearmiss_floor=0.65`, `quran_min_match_words=6`,
`quran_min_margin=0.10` — all tunable. These starting values are conservative on purpose;
we tune them against real khutbah data AFTER the mechanism is proven, never to pass a test.

## Out of scope (do not build here)
Display styling (MB-017), end-to-end mic→TV (MB-018). This ticket ends at: given Arabic
text, correctly classify + return the right render payload.
