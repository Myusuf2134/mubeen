"""STAGE 5 acceptance tests: Render contract + wiring (MB-016).

Tests verify:
- CONFIRMED renders canonical Uthmani + Yusuf Ali + ref_label; source="scripture"; machine_generated=False
- NEAR_MISS renders machine path; source="machine"; machine_generated=True; logged+flagged
- NOT_SCRIPTURE renders machine path; source="machine"; machine_generated=True; not logged
- CONFIRMED NEVER renders model output (only corpus text)
- Wiring behind MB-015 is_scripture() seam works
"""

from __future__ import annotations

import pytest

from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_decision import MatchState, QuranDecision
from mubeen.services.quran_matcher import get_quran_matcher
from mubeen.services.quran_render import RenderPayload, render_from_decision


class TestRenderContractConfirmed:
    """CONFIRMED state render contract."""

    @pytest.mark.asyncio
    async def test_confirmed_renders_canonical_uthmani(self) -> None:
        """CONFIRMED must render canonical Uthmani from corpus, never model output."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision_engine = QuranDecision()

        # Match 2:255
        ayah_2_255_normalized = corpus.get_normalized_text(2, 255)
        match_with_second = await matcher.match(ayah_2_255_normalized)
        decision = decision_engine.decide(match_with_second)

        assert decision.state == MatchState.CONFIRMED

        # Render
        payload = await render_from_decision(decision, ayah_2_255_normalized)

        assert payload is not None
        assert payload.surah == 2
        assert payload.ayah == 255
        assert payload.ref_label == "2:255"

        # CRITICAL: Rendered text must be canonical Uthmani from corpus
        canonical_ayah = corpus.get_ayah(2, 255)
        assert payload.text == canonical_ayah.arabic_uthmani
        assert payload.translation == canonical_ayah.yusuf_ali_en

        # Verify it's not model output (corpus text is byte-for-byte from Tanzil, with diacritics)
        assert len(payload.text) > 0, "Rendered text must not be empty"
        # Tanzil corpus has Unicode marks and variant alif forms
        assert len(payload.text) > 50, "Rendered text must be full Qur'anic verse (not empty/truncated)"

    @pytest.mark.asyncio
    async def test_confirmed_sets_scripture_metadata(self) -> None:
        """CONFIRMED must set source='scripture', machine_generated=False."""
        corpus = await get_quran_corpus()
        matcher = await get_quran_matcher()
        decision_engine = QuranDecision()

        # Match 1:1
        ayah_1_1_normalized = corpus.get_normalized_text(1, 1)
        match_with_second = await matcher.match(ayah_1_1_normalized)
        decision = decision_engine.decide(match_with_second)

        payload = await render_from_decision(decision, ayah_1_1_normalized)

        assert payload is not None
        assert payload.source == "scripture"
        assert payload.machine_generated is False
        assert payload.decision_state == MatchState.CONFIRMED


class TestRenderContractNearMiss:
    """NEAR_MISS state render contract."""

    @pytest.mark.asyncio
    async def test_near_miss_machine_path_logged_flagged(self) -> None:
        """NEAR_MISS must use machine path, set source='machine', log+flag details."""
        matcher = await get_quran_matcher()
        decision_engine = QuranDecision()

        # Create a high-score match that will be NEAR_MISS due to thin margin
        from mubeen.services.quran_matcher import MatchWithSecondBest, MatchResult

        # NEAR_MISS requires >= 6 words but score/margin doesn't pass
        # "الله لا الاه الا هو الحي" = 6 words
        match_result = MatchResult(
            surah=2,
            ayah=255,
            ref_label="2:255",
            score=0.87,  # < 0.85 or margin too thin
            matched_span="الله لا الاه الا هو الحي",  # 6 words
            candidate_ayah_normalized="الله لا الاه الا هو الحي القيوم",
            coverage_of_candidate=0.5,
        )
        match_with_second = MatchWithSecondBest(
            best=match_result,
            second_best_score=0.83,  # margin = 0.04 < min_margin (0.10)
            is_ambiguous=False,
            ambiguous_candidates=[],
        )

        decision = decision_engine.decide(match_with_second)
        assert decision.state == MatchState.NEAR_MISS

        payload = await render_from_decision(decision, "الله لا الاه الا هو الحي")

        assert payload is not None
        assert payload.source == "machine"
        assert payload.machine_generated is True
        assert payload.decision_state == MatchState.NEAR_MISS
        # Payload should contain ref for logging/flagging
        assert payload.ref_label == "2:255"


class TestRenderContractNotScripture:
    """NOT_SCRIPTURE state render contract."""

    @pytest.mark.asyncio
    async def test_not_scripture_machine_path_not_logged(self) -> None:
        """NOT_SCRIPTURE must use machine path, NOT logged."""
        matcher = await get_quran_matcher()
        decision_engine = QuranDecision()

        # Random non-Qur'an text should be NOT_SCRIPTURE
        random_text = "كمبيوتر الحديثة والتقنية"
        match_with_second = await matcher.match(random_text)
        decision = decision_engine.decide(match_with_second)

        assert decision.state == MatchState.NOT_SCRIPTURE

        payload = await render_from_decision(decision, random_text)

        assert payload is not None
        assert payload.source == "machine"
        assert payload.machine_generated is True
        assert payload.decision_state == MatchState.NOT_SCRIPTURE
        # NOT_SCRIPTURE shouldn't have ref for logging
        assert payload.ref_label is None


class TestRenderWiringBehindIsScriptureSeam:
    """Verify wiring behind MB-015 is_scripture() seam."""

    @pytest.mark.asyncio
    async def test_is_scripture_seam_confirmed_returns_true(self) -> None:
        """is_scripture() returns True for CONFIRMED matches."""
        from mubeen.services.quran_render import is_scripture_with_render
        from mubeen.services.quran_corpus import get_quran_corpus

        corpus = await get_quran_corpus()

        # Known complete ayah
        ayah_2_255 = corpus.get_normalized_text(2, 255)
        is_scripture, payload = await is_scripture_with_render(ayah_2_255, ayah_2_255)

        assert is_scripture is True
        assert payload is not None
        assert payload.source == "scripture"
        assert payload.machine_generated is False

    @pytest.mark.asyncio
    async def test_is_scripture_seam_not_scripture_returns_false(self) -> None:
        """is_scripture() returns False for NOT_SCRIPTURE."""
        from mubeen.services.quran_render import is_scripture_with_render

        random_text = "كمبيوتر الحديثة"
        is_scripture, payload = await is_scripture_with_render(random_text, random_text)

        # Should return False (not scripture)
        assert is_scripture is False
        assert payload is not None
        assert payload.source == "machine"
        assert payload.machine_generated is True

    @pytest.mark.asyncio
    async def test_is_scripture_seam_near_miss_returns_false(self) -> None:
        """is_scripture() returns False for NEAR_MISS (not yet confident)."""
        from mubeen.services.quran_render import is_scripture_with_render
        from mubeen.services.quran_corpus import get_quran_corpus

        corpus = await get_quran_corpus()

        # 6-word opening of 2:255 (ambiguous with 3:2, so NEAR_MISS)
        ayah_2_255 = corpus.get_normalized_text(2, 255)
        words = ayah_2_255.split()
        partial_6_words = " ".join(words[:6])

        is_scripture, payload = await is_scripture_with_render(
            partial_6_words, partial_6_words
        )

        # Should return False (ambiguous, not yet confirmed as scripture)
        assert is_scripture is False
        assert payload is not None
        assert payload.source == "machine"  # Falls back to MT


class TestRenderContractInvariants:
    """Verify render contract invariants."""

    @pytest.mark.asyncio
    async def test_confirmed_never_renders_model_output(self) -> None:
        """CONFIRMED renders ONLY canonical corpus text, never GPT output."""
        from mubeen.services.quran_render import is_scripture_with_render
        from mubeen.services.quran_corpus import get_quran_corpus

        corpus = await get_quran_corpus()

        # Test multiple known ayat
        test_refs = [(1, 1), (2, 255), (112, 1)]

        for surah, ayah in test_refs:
            canonical = corpus.get_ayah(surah, ayah)
            if canonical is None:
                continue

            normalized = corpus.get_normalized_text(surah, ayah)
            is_scripture, payload = await is_scripture_with_render(
                normalized, normalized
            )

            if is_scripture:
                # Rendered text must be from corpus, byte-for-byte unchanged
                assert payload.text == canonical.arabic_uthmani, (
                    f"CONFIRMED {surah}:{ayah} rendered text must be canonical corpus text"
                )
                # Translation must be from corpus
                assert payload.translation == canonical.yusuf_ali_en, (
                    f"CONFIRMED {surah}:{ayah} translation must be from corpus"
                )

    @pytest.mark.asyncio
    async def test_render_payload_fields_present_for_confirmed(self) -> None:
        """CONFIRMED payload must have all required render fields."""
        from mubeen.services.quran_render import is_scripture_with_render
        from mubeen.services.quran_corpus import get_quran_corpus

        corpus = await get_quran_corpus()
        ayah_1_1 = corpus.get_normalized_text(1, 1)

        is_scripture, payload = await is_scripture_with_render(ayah_1_1, ayah_1_1)

        assert is_scripture is True
        assert payload is not None

        # CONFIRMED payload must have these fields populated
        required_fields = [
            "text",  # Canonical Uthmani
            "source_text",  # Original input
            "source",  # "scripture"
            "machine_generated",  # False
            "surah",  # Number
            "ayah",  # Number
            "ref_label",  # "surah:ayah"
            "translation",  # Yusuf Ali
        ]

        for field in required_fields:
            assert hasattr(payload, field), f"Payload missing required field: {field}"
            value = getattr(payload, field)
            assert value is not None, f"Payload field {field} must not be None for CONFIRMED"
