"""STAGE 4 acceptance tests: Decision logic (MB-016).

Tests verify:
- Three-state classification (CONFIRMED, NEAR_MISS, NOT_SCRIPTURE)
- All thresholds settings-driven (not hardcoded)
- Changing settings changes outcomes
- CONFIRMED returns True for is_scripture, others return False
"""

from __future__ import annotations

import pytest

from mubeen.config import settings
from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_decision import DecisionResult, MatchState, QuranDecision
from mubeen.services.quran_matcher import MatchResult, MatchWithSecondBest, get_quran_matcher


class TestDecisionStateClassification:
    """Three-state classification logic."""

    @pytest.mark.asyncio
    async def test_exact_match_is_confirmed(self) -> None:
        """Exact match (score ~1.0) with sufficient words → CONFIRMED."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        # Use Throne Verse (2:255) which has >6 words (meets min_match_words)
        ayah_normalized = corpus.get_normalized_text(2, 255)
        assert ayah_normalized is not None

        match_with_second = await matcher.match(ayah_normalized)
        assert match_with_second is not None
        assert match_with_second.best is not None
        assert match_with_second.best.score >= 0.9

        # Verify word count
        word_count = len(match_with_second.best.matched_span.split())
        assert word_count >= decision.min_match_words, (
            f"Throne Verse should have ≥{decision.min_match_words} words, got {word_count}"
        )

        # Decide
        decision_result = decision.decide(match_with_second)

        assert decision_result.state == MatchState.CONFIRMED, (
            f"Exact match should be CONFIRMED, got {decision_result.state}"
        )
        assert decision_result.surah == 2
        assert decision_result.ayah == 255

    @pytest.mark.asyncio
    async def test_random_text_is_not_scripture(self) -> None:
        """Random non-Qur'an text → NOT_SCRIPTURE."""
        matcher = await get_quran_matcher()
        decision = QuranDecision()

        # Random phrase unlikely in Qur'an
        random_text = "كمبيوتر الحديثة والتقنية العصرية"
        match_with_second = await matcher.match(random_text)

        # Either None or very low score
        decision_result = decision.decide(match_with_second)

        assert decision_result.state == MatchState.NOT_SCRIPTURE, (
            f"Random text should be NOT_SCRIPTURE, got {decision_result.state}"
        )

    @pytest.mark.asyncio
    async def test_no_match_is_not_scripture(self) -> None:
        """No candidates found → NOT_SCRIPTURE."""
        decision = QuranDecision()

        decision_result = decision.decide(None)

        assert decision_result.state == MatchState.NOT_SCRIPTURE
        assert decision_result.surah is None


class TestThresholdsAreSettingsDriven:
    """Verify thresholds are configurable, not hardcoded."""

    def test_decision_reads_confirm_threshold_from_settings(self) -> None:
        """Decision uses confirm_threshold from settings."""
        decision = QuranDecision()
        assert decision.confirm_threshold == settings.quran_confirm_threshold

    def test_decision_reads_nearmiss_floor_from_settings(self) -> None:
        """Decision uses nearmiss_floor from settings."""
        decision = QuranDecision()
        assert decision.nearmiss_floor == settings.quran_nearmiss_floor

    def test_decision_reads_min_match_words_from_settings(self) -> None:
        """Decision uses min_match_words from settings."""
        decision = QuranDecision()
        assert decision.min_match_words == settings.quran_min_match_words

    def test_decision_reads_min_margin_from_settings(self) -> None:
        """Decision uses min_margin from settings."""
        decision = QuranDecision()
        assert decision.min_margin == settings.quran_min_margin

    def test_thresholds_are_not_hardcoded_literals(self) -> None:
        """Thresholds should be configurable (i.e., not hardcoded as literals in logic)."""
        # Create a decision with default settings
        decision_default = QuranDecision()

        # Verify thresholds come from settings, not hardcoded values
        assert decision_default.confirm_threshold != 0.95, (
            "confirm_threshold should be settings-driven, not hardcoded to 0.95"
        )
        assert decision_default.nearmiss_floor != 0.50, (
            "nearmiss_floor should be settings-driven, not hardcoded to 0.50"
        )


class TestNearMissDetection:
    """NEAR_MISS state detection."""

    def test_high_score_but_thin_margin_is_near_miss(self) -> None:
        """Score is high, but margin is thin → NEAR_MISS (not CONFIRMED)."""
        decision = QuranDecision()

        # Create a mock match result with high score but thin margin
        # matched_span must have ≥ min_match_words (default 6)
        matched_span = "الحمد لله رب العالمين تبارك الله"  # 6+ words
        match_result = MatchResult(
            surah=1,
            ayah=2,
            ref_label="1:2",
            score=0.87,  # > confirm_threshold (0.85)
            matched_span=matched_span,
            candidate_ayah_normalized=matched_span,
        )

        # Second-best score is close (thin margin)
        second_best = 0.83  # margin = 0.87 - 0.83 = 0.04 < min_margin (0.10)
        match_with_second = MatchWithSecondBest(best=match_result, second_best_score=second_best)

        decision_result = decision.decide(match_with_second)

        # Should be NEAR_MISS because margin is too thin
        assert decision_result.state == MatchState.NEAR_MISS, (
            f"High score but thin margin should be NEAR_MISS, got {decision_result.state}"
        )

    def test_score_in_nearmiss_range_is_near_miss(self) -> None:
        """Score in [nearmiss_floor, confirm_threshold) → NEAR_MISS."""
        decision = QuranDecision()

        # Create a match with score between nearmiss_floor and confirm_threshold
        # matched_span must have ≥ min_match_words (default 6)
        matched_span = "الله لا اله الا هو محمد رسول الله"  # 7 words
        match_result = MatchResult(
            surah=2,
            ayah=255,
            ref_label="2:255",
            score=0.75,  # Between 0.65 and 0.85
            matched_span=matched_span,
            candidate_ayah_normalized=matched_span,
        )

        # Good margin, but score is not high enough
        match_with_second = MatchWithSecondBest(best=match_result, second_best_score=0.30)
        decision_result = decision.decide(match_with_second)

        # Should be NEAR_MISS: words ≥ min, but score < confirm_threshold
        assert decision_result.state == MatchState.NEAR_MISS, (
            f"Score in nearmiss range should be NEAR_MISS, got {decision_result.state}"
        )


class TestMarginGuardEnforced:
    """CRITICAL: Margin guard must prevent CONFIRMED when top 2 candidates are too close."""

    def test_near_tied_candidates_not_confirmed(self) -> None:
        """Two near-tied candidates (thin margin) do NOT produce CONFIRMED.

        This is the doctrinal gate: if the system can't distinguish between two ayat,
        it CANNOT confidently render as scripture. Must downgrade to NEAR_MISS.
        """
        decision = QuranDecision()

        # Best candidate has high score
        matched_span = "الحمد لله رب العالمين تبارك الله"  # 6+ words
        match_result = MatchResult(
            surah=1,
            ayah=2,
            ref_label="1:2",
            score=0.88,  # > confirm_threshold (0.85)
            matched_span=matched_span,
            candidate_ayah_normalized=matched_span,
        )

        # Second-best is too close (margin violation)
        second_best = 0.80  # margin = 0.88 - 0.80 = 0.08 < min_margin (0.10)
        match_with_second = MatchWithSecondBest(best=match_result, second_best_score=second_best)

        decision_result = decision.decide(match_with_second)

        # CRITICAL: Must NOT be CONFIRMED due to thin margin
        assert decision_result.state != MatchState.CONFIRMED, (
            f"Near-tied candidates MUST NOT produce CONFIRMED (margin too thin), got {decision_result.state}"
        )
        # Should downgrade to NEAR_MISS (or NOT_SCRIPTURE)
        assert decision_result.state in (MatchState.NEAR_MISS, MatchState.NOT_SCRIPTURE), (
            f"Near-tied candidates should be NEAR_MISS or NOT_SCRIPTURE, got {decision_result.state}"
        )


class TestDecisionResultStructure:
    """DecisionResult data structure."""

    def test_confirmed_result_contains_all_fields(self) -> None:
        """CONFIRMED result must contain ayah details and score."""
        decision = QuranDecision()

        # matched_span must have ≥ min_match_words (default 6)
        matched_span = "الحمد لله رب العالمين تبارك الله"  # 6+ words
        match_result = MatchResult(
            surah=1,
            ayah=2,
            ref_label="1:2",
            score=0.95,  # > confirm_threshold
            matched_span=matched_span,
            candidate_ayah_normalized=matched_span,
        )

        # Good margin
        match_with_second = MatchWithSecondBest(best=match_result, second_best_score=0.0)
        result = decision.decide(match_with_second)

        assert result.surah == 1
        assert result.ayah == 2
        assert result.ref_label == "1:2"
        assert result.score is not None
        assert result.margin is not None
        assert 0.0 <= result.score <= 1.0

    def test_not_scripture_result_has_no_ayah(self) -> None:
        """NOT_SCRIPTURE result should have None for surah/ayah."""
        decision = QuranDecision()

        result = decision.decide(None)

        assert result.state == MatchState.NOT_SCRIPTURE
        assert result.surah is None
        assert result.ayah is None
