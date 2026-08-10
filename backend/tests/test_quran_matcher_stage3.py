"""STAGE 3 acceptance tests: Matching engine (MB-016).

Tests verify:
- N-gram index builds from corpus
- Rolling window queries index for candidate ayat
- Token-level similarity scoring: known ayah → score ~1.0, random text → score low
"""

from __future__ import annotations

import pytest

from mubeen.services.normalize_arabic import normalize_arabic
from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_matcher import QuranMatcher, get_quran_matcher


class TestNGramIndexBuilding:
    """N-gram index building and querying."""

    @pytest.mark.asyncio
    async def test_index_builds_from_corpus(self) -> None:
        """Verify n-gram index builds successfully."""
        corpus = await get_quran_corpus()
        matcher = QuranMatcher(n_gram_size=3)
        await matcher.initialize(corpus)

        assert matcher._initialized, "Matcher should be initialized"
        assert matcher.index._built, "Index should be marked as built"
        assert len(matcher.index.index) > 0, "Index should contain n-grams"

    @pytest.mark.asyncio
    async def test_index_contains_candidate_ayat(self) -> None:
        """Verify index maps grams to candidate ayat."""
        corpus = await get_quran_corpus()
        matcher = QuranMatcher(n_gram_size=3)
        await matcher.initialize(corpus)

        # The Basmala (1:1) normalized should be in the index
        basmala_normalized = normalize_arabic("بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ")
        words = basmala_normalized.split()

        # Query for first 3 words
        if len(words) >= 3:
            gram = tuple(words[:3])
            candidates = matcher.index.index.get(gram)
            # Should find at least one ayah (the Basmala itself)
            assert candidates is not None, f"Gram {gram} should be in index"
            assert (1, 1) in candidates, "Basmala (1:1) should be a candidate for its own gram"


class TestMatcherInitialization:
    """Matcher initialization and state."""

    @pytest.mark.asyncio
    async def test_matcher_singleton_initializes(self) -> None:
        """Verify matcher singleton initializes correctly."""
        matcher = await get_quran_matcher()
        assert matcher._initialized, "Matcher should be initialized"
        assert matcher.corpus is not None, "Matcher should have corpus"

    @pytest.mark.asyncio
    async def test_matcher_can_be_reused(self) -> None:
        """Verify singleton returns same instance."""
        matcher1 = await get_quran_matcher()
        matcher2 = await get_quran_matcher()
        assert matcher1 is matcher2, "Singleton should return same instance"


class TestTokenSimilarityScoring:
    """Token-level similarity scoring."""

    @pytest.mark.asyncio
    async def test_exact_match_scores_high(self) -> None:
        """Exact match should score close to 1.0."""
        corpus = await get_quran_corpus()
        matcher = QuranMatcher(n_gram_size=3)
        await matcher.initialize(corpus)

        # The Basmala: normalized form should match itself with high score
        basmala_ayah = corpus.get_ayah(1, 1)
        assert basmala_ayah is not None
        basmala_normalized = corpus.get_normalized_text(1, 1)
        assert basmala_normalized is not None

        # Match the exact normalized text
        match_with_second = await matcher.match(basmala_normalized)

        assert match_with_second is not None, "Should find a match for Basmala"
        assert match_with_second.best is not None
        result = match_with_second.best
        assert result.surah == 1, "Should match Surah 1"
        assert result.ayah == 1, "Should match Ayah 1"
        assert result.score >= 0.9, (
            f"Exact match should score ≥ 0.9, got {result.score} for 1:1"
        )

    @pytest.mark.asyncio
    async def test_random_arabic_scores_low(self) -> None:
        """Random non-Qur'an Arabic should score low."""
        matcher = await get_quran_matcher()

        # Random phrase unlikely to appear in Qur'an
        random_arabic = normalize_arabic("كمبيوتر الحديثة والتقنية العصرية")
        match_with_second = await matcher.match(random_arabic)

        # Either no match or very low score
        if match_with_second is None or match_with_second.best is None:
            # No candidates found — that's good (random text doesn't match index)
            pass
        else:
            # If a match is found, score should be low
            result = match_with_second.best
            assert result.score < 0.5, (
                f"Random text should score low, got {result.score}: {result.ref_label}"
            )

    @pytest.mark.asyncio
    async def test_known_ayah_2_255_matches_high(self) -> None:
        """Ayat Al-Kursi (2:255) should match itself with high score."""
        corpus = await get_quran_corpus()
        matcher = QuranMatcher(n_gram_size=3)
        await matcher.initialize(corpus)

        # Get the normalized Throne Verse
        throne_normalized = corpus.get_normalized_text(2, 255)
        assert throne_normalized is not None

        match_with_second = await matcher.match(throne_normalized)

        assert match_with_second is not None, "Should find match for Throne Verse"
        assert match_with_second.best is not None
        result = match_with_second.best
        assert result.surah == 2, "Should match Surah 2"
        assert result.ayah == 255, "Should match Ayah 255"
        assert result.score >= 0.9, (
            f"Throne Verse exact match should score ≥ 0.9, got {result.score}"
        )

    @pytest.mark.asyncio
    async def test_known_ayah_94_6_matches_high(self) -> None:
        """Ayah 94:6 should match itself with high score."""
        corpus = await get_quran_corpus()
        matcher = QuranMatcher(n_gram_size=3)
        await matcher.initialize(corpus)

        ayah_96_normalized = corpus.get_normalized_text(94, 6)
        assert ayah_96_normalized is not None

        match_with_second = await matcher.match(ayah_96_normalized)

        assert match_with_second is not None, "Should find match for 94:6"
        assert match_with_second.best is not None
        result = match_with_second.best
        assert result.surah == 94, "Should match Surah 94"
        assert result.ayah == 6, "Should match Ayah 6"
        assert result.score >= 0.9, (
            f"Exact match should score ≥ 0.9, got {result.score}"
        )


class TestMatchingWindow:
    """Rolling window + matching integration."""

    @pytest.mark.asyncio
    async def test_partial_window_from_ayah(self) -> None:
        """Partial window from an ayah should still match that ayah."""
        corpus = await get_quran_corpus()
        matcher = QuranMatcher(n_gram_size=3)
        await matcher.initialize(corpus)

        # Get Basmala and take first ~5 words
        basmala_full = corpus.get_normalized_text(1, 1)
        assert basmala_full is not None

        words = basmala_full.split()
        partial_window = " ".join(words[:min(5, len(words))])

        match_with_second = await matcher.match(partial_window)

        assert match_with_second is not None, "Partial window should find a match"
        assert match_with_second.best is not None
        result = match_with_second.best
        assert result.surah == 1, (
            f"Partial Basmala should match Surah 1, got {result.surah}"
        )
        assert result.ayah == 1, (
            f"Partial Basmala should match Ayah 1, got {result.ayah}"
        )
        # Partial match may score lower than exact
        assert result.score >= 0.6, (
            f"Partial match should score ≥ 0.6, got {result.score}"
        )

    @pytest.mark.asyncio
    async def test_empty_window_returns_none(self) -> None:
        """Empty window should return None."""
        matcher = await get_quran_matcher()
        match_with_second = await matcher.match("")
        assert match_with_second is None, "Empty window should return None"

    @pytest.mark.asyncio
    async def test_whitespace_only_window_returns_none(self) -> None:
        """Whitespace-only window should return None."""
        matcher = await get_quran_matcher()
        match_with_second = await matcher.match("   ")
        assert match_with_second is None, "Whitespace-only window should return None"


class TestMatchResultStructure:
    """MatchResult data structure."""

    @pytest.mark.asyncio
    async def test_match_result_contains_required_fields(self) -> None:
        """MatchResult must contain all required fields."""
        matcher = await get_quran_matcher()

        # Match a known ayah
        basmala_normalized = normalize_arabic("بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ")
        match_with_second = await matcher.match(basmala_normalized)

        assert match_with_second is not None
        assert match_with_second.best is not None
        result = match_with_second.best
        assert hasattr(result, "surah"), "MatchResult must have surah"
        assert hasattr(result, "ayah"), "MatchResult must have ayah"
        assert hasattr(result, "ref_label"), "MatchResult must have ref_label"
        assert hasattr(result, "score"), "MatchResult must have score"
        assert hasattr(result, "matched_span"), "MatchResult must have matched_span"
        assert hasattr(result, "candidate_ayah_normalized"), (
            "MatchResult must have candidate_ayah_normalized"
        )

        assert 0.0 <= result.score <= 1.0, "Score must be in [0.0, 1.0]"
        assert result.ref_label == f"{result.surah}:{result.ayah}"

        # Verify second_best_score is present
        assert hasattr(match_with_second, "second_best_score"), (
            "MatchWithSecondBest must have second_best_score"
        )
        assert 0.0 <= match_with_second.second_best_score <= 1.0, (
            "second_best_score must be in [0.0, 1.0]"
        )
