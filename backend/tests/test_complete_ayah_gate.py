"""Tests for complete-ayah gate: allow CONFIRMED for short complete ayat.

Short complete ayat (like 112:1, 103:1) should CONFIRM even if < min_match_words.
Short fragments (like "الحمد لله" from 1:2) should NOT CONFIRM.
Shared openings (like 2:255/3:2) still guarded by ambiguity check.
"""

from __future__ import annotations

import pytest

from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_decision import MatchState, QuranDecision
from mubeen.services.quran_matcher import get_quran_matcher


class TestCompleteAyahGate:
    """Complete-ayah gate allows short CONFIRMED if entire ayah is recited."""

    @pytest.mark.asyncio
    async def test_full_ayah_sweep_short_ayat_confirm(self) -> None:
        """Short complete ayat (1:1, 112:1, etc.) should CONFIRM when said in full."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        # Select known short ayat to test
        test_ayat = [
            (1, 1),    # Basmala (4 words)
            (1, 2),    # Al-Fatiha verse 2 (4 words)
            (112, 1),  # Surah Ikhlas (4 words: قل هو الله احد)
            (103, 1),  # Surah Al-Asr (3 words)
            (108, 1),  # Surah Al-Kawthar (2 words)
            (94, 6),   # Ad-Dhuha verse 6 (5 words)
        ]

        results = []
        for surah, ayah in test_ayat:
            ayah_normalized = corpus.get_normalized_text(surah, ayah)
            if ayah_normalized is None:
                continue

            word_count = len(ayah_normalized.split())
            match_with_second = await matcher.match(ayah_normalized)
            assert match_with_second is not None and match_with_second.best is not None

            result = match_with_second.best
            decision_result = decision.decide(match_with_second)

            results.append({
                "ref": f"{surah}:{ayah}",
                "words": word_count,
                "score": result.score,
                "coverage": result.coverage_of_candidate,
                "state": decision_result.state,
                "correct_ref": result.ref_label == f"{surah}:{ayah}",
            })

            # CRITICAL: Complete short ayah must CONFIRM
            assert (
                decision_result.state == MatchState.CONFIRMED
                and result.ref_label == f"{surah}:{ayah}"
            ), (
                f"Short complete ayah {surah}:{ayah} should CONFIRM as itself, "
                f"got {result.ref_label} state={decision_result.state}"
            )

        # Print summary
        print("\n=== Complete Ayah Gate Test Results ===")
        for r in results:
            status = "✓" if r["state"] == MatchState.CONFIRMED and r["correct_ref"] else "✗"
            print(
                f"{status} {r['ref']:5} ({r['words']:2} words): "
                f"score={r['score']:.3f}, coverage={r['coverage']:.2f}, "
                f"state={r['state'].value}, matches={r['correct_ref']}"
            )

    @pytest.mark.asyncio
    async def test_fragment_alhamdulillah_not_scripture(self) -> None:
        """Short phrase 'الحمد لله رب' (3 words) should NOT CONFIRM (fragment, not complete ayah)."""
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        # "الحمد لله رب" is fragment of 1:2 (4 words), not a complete ayah
        # Using 3 words so it's in the n-gram index but still a fragment
        fragment_text = "الحمد لله رب"

        match_with_second = await matcher.match(fragment_text)

        # Fragment may or may not find matches, but if it does, should NOT CONFIRM
        if match_with_second is not None and match_with_second.best is not None:
            result = match_with_second.best
            decision_result = decision.decide(match_with_second)

            # Fragment (< 90% coverage of any candidate) should NOT CONFIRM
            assert decision_result.state != MatchState.CONFIRMED, (
                f"Fragment '{fragment_text}' should NOT CONFIRM, "
                f"got {result.ref_label} state={decision_result.state}, coverage={result.coverage_of_candidate:.2f}"
            )

            print(
                f"\n✓ Fragment '{fragment_text}' correctly NOT CONFIRMED "
                f"(matched {result.ref_label}, state={decision_result.state}, "
                f"coverage={result.coverage_of_candidate:.2f})"
            )
        else:
            # No matches found is also acceptable (fragment too short for index)
            print(f"\n✓ Fragment '{fragment_text}' no matches found (acceptable)")

    @pytest.mark.asyncio
    async def test_2_255_ladder_no_shared_opening_confirm(self) -> None:
        """6, 8, 12-word windows from 2:255 should not confirm as 3:2 (ambiguity guard)."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        ayah_2_255_normalized = corpus.get_normalized_text(2, 255)
        assert ayah_2_255_normalized is not None

        words_2_255 = ayah_2_255_normalized.split()

        test_windows = [6, 8, 12]
        for window_size in test_windows:
            if window_size > len(words_2_255):
                continue

            window = " ".join(words_2_255[:window_size])
            match_with_second = await matcher.match(window)
            assert match_with_second is not None
            assert match_with_second.best is not None

            result = match_with_second.best
            decision_result = decision.decide(match_with_second)

            # Should never confirm as 3:2
            is_3_2 = result.surah == 3 and result.ayah == 2
            assert not is_3_2 or decision_result.state != MatchState.CONFIRMED, (
                f"{window_size}-word window from 2:255 should NOT CONFIRM as 3:2, "
                f"got state={decision_result.state}, ambiguous={match_with_second.is_ambiguous}"
            )

            print(
                f"✓ {window_size}-word from 2:255: "
                f"matched {result.ref_label} (state={decision_result.state}, "
                f"ambiguous={match_with_second.is_ambiguous})"
            )
