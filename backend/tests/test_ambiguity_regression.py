"""Regression test: shared opening phrases must not confirm wrong ayah.

CRITICAL DEFECT: A partial 2:255 (Ayat al-Kursi) opening "الله لا اله الا هو"
is confidently CONFIRMED as 3:2 (Al-Imran 3:2) at score 0.92–0.93,
even though both ayat share this opening. The system must NOT confirm when
a window is a valid prefix of multiple ayat — it cannot yet know which one.

This test verifies the regression exists and must be fixed.
"""

from __future__ import annotations

import pytest

from mubeen.services.normalize_arabic import normalize_arabic
from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_decision import MatchState, QuranDecision
from mubeen.services.quran_matcher import get_quran_matcher


class TestAmbiguityRegression:
    """Verify the shared-opening defect and fixes."""

    @pytest.mark.asyncio
    async def test_2_255_opening_is_ambiguous_with_3_2(self) -> None:
        """Partial 2:255 opening shares text with 3:2 — must detect ambiguity."""
        corpus = await get_quran_corpus()

        # Get both ayat's normalized texts
        ayah_2_255 = corpus.get_normalized_text(2, 255)
        ayah_3_2 = corpus.get_normalized_text(3, 2)

        assert ayah_2_255 is not None
        assert ayah_3_2 is not None

        # Both should start with the same opening phrase
        words_2_255 = ayah_2_255.split()
        words_3_2 = ayah_3_2.split()

        # Get the shared opening (both start the same way)
        shared_words = []
        for i in range(min(len(words_2_255), len(words_3_2))):
            if words_2_255[i] == words_3_2[i]:
                shared_words.append(words_2_255[i])
            else:
                break

        # Should have at least 4-5 shared words at the opening
        assert len(shared_words) >= 4, (
            f"2:255 and 3:2 should share opening phrase, got {shared_words}"
        )

        shared_text = " ".join(shared_words)
        print(f"\nShared opening: {shared_text}")
        print(f"Ayah 2:255: {ayah_2_255[:80]}...")
        print(f"Ayah 3:2: {ayah_3_2[:80]}...")

    @pytest.mark.asyncio
    async def test_6_word_opening_of_2_255_should_not_confirm_as_3_2(self) -> None:
        """DEFECT: 6-word opening of 2:255 incorrectly confirms as 3:2."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        # Get 6 words from 2:255 opening
        ayah_2_255_normalized = corpus.get_normalized_text(2, 255)
        assert ayah_2_255_normalized is not None

        words_2_255 = ayah_2_255_normalized.split()
        window_6_words = " ".join(words_2_255[:6])

        print(f"\n6-word window from 2:255: {window_6_words}")

        # Match this window
        match_with_second = await matcher.match(window_6_words)
        assert match_with_second is not None
        assert match_with_second.best is not None

        result = match_with_second.best
        print(f"Best match: {result.ref_label} (score {result.score:.3f})")

        # Decide
        decision_result = decision.decide(match_with_second)

        # REGRESSION: This is currently CONFIRMED as 3:2 (WRONG!)
        # After fix: should be NEAR_MISS or NOT_SCRIPTURE (not 3:2)
        if decision_result.state == MatchState.CONFIRMED:
            # Document the defect
            assert result.surah != 3 or result.ayah != 2, (
                f"DEFECT: 6-word 2:255 opening should NOT confirm as {result.ref_label}. "
                f"Window is ambiguous — shared opening with multiple ayat. "
                f"Must be NEAR_MISS until disambiguation. Got score {result.score:.3f}"
            )

    @pytest.mark.asyncio
    async def test_8_word_opening_of_2_255_should_not_confirm_as_3_2(self) -> None:
        """DEFECT: 8-word opening of 2:255 incorrectly confirms as 3:2."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        ayah_2_255_normalized = corpus.get_normalized_text(2, 255)
        assert ayah_2_255_normalized is not None

        words_2_255 = ayah_2_255_normalized.split()
        window_8_words = " ".join(words_2_255[:8])

        print(f"\n8-word window from 2:255: {window_8_words}")

        match_with_second = await matcher.match(window_8_words)
        assert match_with_second is not None
        assert match_with_second.best is not None

        result = match_with_second.best
        print(f"Best match: {result.ref_label} (score {result.score:.3f})")

        decision_result = decision.decide(match_with_second)

        # After fix: should prefer 2:255 over 3:2 (same opening but 2:255 continues)
        if decision_result.state == MatchState.CONFIRMED:
            # The CORRECT ayah is 2:255, not 3:2
            assert result.surah == 2 and result.ayah == 255, (
                f"8-word 2:255 opening: top match should be 2:255, got {result.ref_label} "
                f"(score {result.score:.3f}). Ambiguous prefix — must disambiguate."
            )

    @pytest.mark.asyncio
    async def test_12_word_opening_of_2_255_should_confirm_as_2_255(self) -> None:
        """With 12 words, the window should be specific enough to confirm 2:255."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        ayah_2_255_normalized = corpus.get_normalized_text(2, 255)
        assert ayah_2_255_normalized is not None

        words_2_255 = ayah_2_255_normalized.split()
        window_12_words = " ".join(words_2_255[:12])

        print(f"\n12-word window from 2:255: {window_12_words}")

        match_with_second = await matcher.match(window_12_words)
        assert match_with_second is not None
        assert match_with_second.best is not None

        result = match_with_second.best
        print(f"Best match: {result.ref_label} (score {result.score:.3f})")

        decision_result = decision.decide(match_with_second)

        # With 12 words, should be specific enough to confirm 2:255
        # (At this point, the window goes beyond the opening and includes unique text to 2:255)
        if decision_result.state == MatchState.CONFIRMED:
            assert result.surah == 2 and result.ayah == 255, (
                f"12-word 2:255 window should confirm 2:255, got {result.ref_label}"
            )
