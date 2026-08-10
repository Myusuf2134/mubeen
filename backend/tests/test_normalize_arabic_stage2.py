"""STAGE 2 acceptance tests: Arabic normalization (MB-016).

Tests verify:
- normalize_arabic is idempotent
- Unit tests against known (raw → normalized) pairs from Qur'an
- Same function used in corpus indexing and matching
"""

from __future__ import annotations

import pytest

from mubeen.services.normalize_arabic import normalize_arabic
from mubeen.services.quran_corpus import get_quran_corpus


class TestNormalizeArabicIdempotence:
    """normalize_arabic must be idempotent: f(f(x)) == f(x)."""

    def test_idempotent_diacritics_removed(self) -> None:
        """Normalizing twice yields same result."""
        text_with_diacritics = "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
        once = normalize_arabic(text_with_diacritics)
        twice = normalize_arabic(once)
        assert once == twice, "Normalization must be idempotent"

    def test_idempotent_already_normalized(self) -> None:
        """Normalizing an already-normalized text is unchanged."""
        normalized = "الحمد لله رب العالمين"
        result = normalize_arabic(normalized)
        assert result == normalized, "Normalized text should be unchanged"

    def test_idempotent_empty_string(self) -> None:
        """Empty string should remain empty."""
        assert normalize_arabic("") == ""
        assert normalize_arabic(normalize_arabic("")) == ""

    def test_idempotent_whitespace_only(self) -> None:
        """Multiple spaces collapse to single space, then stay stable."""
        text = "الحمد    لله    رب"
        once = normalize_arabic(text)
        twice = normalize_arabic(once)
        assert once == twice
        assert once == "الحمد لله رب"


class TestNormalizeArabicPairs:
    """Unit tests against known Qur'anic text pairs."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            # 1:1 — Basmala (with regular diacritics and superscript alif on Rahman)
            ("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "بسم الله الرحمان الرحيم"),
            # 1:2 — Alhamdulillah
            ("الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "الحمد لله رب العالمين"),
            # 1:3 — Maliki yawm ad-din
            ("مَالِكِ يَوْمِ الدِّينِ", "مالك يوم الدين"),
            # 2:255 — Ayat Al-Kursi (first part)
            # Note: diacritics and marks are removed; إ → ا; superscript alif → full alif
            ("اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ", "الله لا الاه الا هو"),
            # Alif forms: ا, أ, إ, آ all normalize to ا
            ("أكل", "اكل"),
            ("إن", "ان"),
            ("آمن", "امن"),
            # Taa marbuta ة → ه
            ("الجنة", "الجنه"),
            ("الآخرة", "الاخره"),
            # Alif maqsura ى → ي
            ("موسى", "موسي"),
            ("الأعلى", "الاعلي"),
            # Hamza carriers: ؤ → و, ئ → ي
            ("مؤمن", "مومن"),
            ("القائم", "القايم"),
            # Whitespace collapse (and note: رحمة → رحمه per taa marbuta normalization)
            ("السلام   عليكم   ورحمة   الله", "السلام عليكم ورحمه الله"),
            # Shadda (doubled consonant marker)
            ("رَبِّ", "رب"),
            ("الدِّينِ", "الدين"),
            # CRITICAL: Tanzil corpus text with wasla (ٱ) and Quranic marks must
            # normalize to SAME string as plain STT output (no wasla, no marks)
            # Corpus: "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ" (with wasla ٱ, superscript marks)
            # STT:    "بسم الله الرحمان الرحيم"                 (plain letters; superscript alif→full alif)
            # Both normalize to same result (marks removed, wasla→alif, superscript→alif)
            ("بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ", "بسم الله الرحمان الرحيم"),
            # Another Tanzil corpus example with wasla and small high marks
            ("ٱلۡحَمۡدُ لِلَّهِ رَبِّ ٱلۡعَٰلَمِينَ", "الحمد لله رب العالمين"),
        ],
    )
    def test_normalize_known_pairs(self, raw: str, expected: str) -> None:
        """Verify normalization against known Qur'anic text pairs."""
        result = normalize_arabic(raw)
        assert result == expected, (
            f"normalize_arabic({raw!r}) = {result!r}, expected {expected!r}"
        )


class TestNormalizeArabicRemovesDiacritics:
    """Verify specific diacritical mark removal."""

    def test_removes_fatha(self) -> None:
        """Fatha (َ) is removed."""
        assert normalize_arabic("كِتَابٌ") == "كتاب"

    def test_removes_damma(self) -> None:
        """Damma (ُ) is removed."""
        assert normalize_arabic("رُبّ") == "رب"

    def test_removes_kasra(self) -> None:
        """Kasra (ِ) is removed."""
        assert normalize_arabic("بِسْمِ") == "بسم"

    def test_removes_sukun(self) -> None:
        """Sukun (ْ) is removed."""
        assert normalize_arabic("سْلَام") == "سلام"

    def test_removes_tanwin(self) -> None:
        """Tanwin (ًٌٍ) is removed."""
        assert normalize_arabic("كِتَابٌ مُؤمِنٍ") == "كتاب مومن"


class TestNormalizeArabicCorpusVsSTT:
    """Verify corpus text with marks normalizes same as plain STT."""

    def test_corpus_with_wasla_equals_plain_stt(self) -> None:
        """Corpus text with wasla (ٱ) normalizes to same result as plain STT."""
        # Corpus version: with wasla alif (ٱ) and diacritics
        corpus_text = "ٱلۡحَمۡدُ لِلَّهِ"
        # Plain STT version: no wasla, no diacritics
        stt_text = "الحمد لله"

        corpus_normalized = normalize_arabic(corpus_text)
        stt_normalized = normalize_arabic(stt_text)

        assert corpus_normalized == stt_normalized, (
            f"Corpus with wasla must normalize same as plain STT:\n"
            f"  Corpus: {corpus_text!r} → {corpus_normalized!r}\n"
            f"  STT:    {stt_text!r} → {stt_normalized!r}"
        )
        assert corpus_normalized == "الحمد لله"

    def test_corpus_with_quranic_marks_equals_plain_stt(self) -> None:
        """Corpus text with Quranic annotation marks normalizes to plain STT."""
        # Corpus version: with superscript alif, small high marks
        corpus_text = "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ"
        # Plain STT version: same content, plain letters
        # Note: superscript alif becomes full alif (الرحمان, not الرحمن)
        stt_text = "بسم الله الرحمان الرحيم"

        corpus_normalized = normalize_arabic(corpus_text)
        stt_normalized = normalize_arabic(stt_text)

        assert corpus_normalized == stt_normalized, (
            f"Corpus with marks must normalize same as plain STT:\n"
            f"  Corpus: {corpus_text!r} → {corpus_normalized!r}\n"
            f"  STT:    {stt_text!r} → {stt_normalized!r}"
        )

    def test_wasla_alif_normalized_to_base_alif(self) -> None:
        """Wasla alif (ٱ U+0671) → base alif (ا)."""
        # "ٱالله" = wasla + alif + alif becomes "ا" + "ا" + "الله" = "االله"
        assert normalize_arabic("ٱالله") == "االله"

    def test_superscript_alif_becomes_full_alif(self) -> None:
        """Superscript alif (ٰ U+0670) → base alif (ا)."""
        # "رَّحۡمَٰنِ" = Rahman in Quranic orthography
        # Should become "رحمان" (superscript alif → full alif)
        assert normalize_arabic("رَّحۡمَٰنِ") == "رحمان"

    def test_quranic_annotation_marks_removed(self) -> None:
        """Quranic annotation marks (U+06D6–U+06ED) are removed."""
        # Using actual marks from Tanzil corpus
        text_with_marks = "اللَّہُۖ"  # includes Quranic mark ۖ
        result = normalize_arabic(text_with_marks)
        # Should not contain any annotation marks
        assert "ۖ" not in result


class TestNormalizeArabicEmptyAndEdgeCases:
    """Edge cases: empty, spaces, special characters."""

    def test_empty_string(self) -> None:
        """Empty string remains empty."""
        assert normalize_arabic("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string becomes empty."""
        assert normalize_arabic("   ") == ""
        assert normalize_arabic("\t\n") == ""

    def test_leading_trailing_whitespace(self) -> None:
        """Leading/trailing whitespace is stripped."""
        assert normalize_arabic("  السلام  ") == "السلام"

    def test_multiple_spaces_between_words(self) -> None:
        """Multiple spaces between words collapse to single space."""
        assert normalize_arabic("السلام   عليكم   ورحمة") == "السلام عليكم ورحمه"

    def test_non_arabic_characters_pass_through(self) -> None:
        """Non-Arabic characters (e.g., numbers, Latin) pass through."""
        # Numbers and Latin letters are preserved (not stripped)
        result = normalize_arabic("السلام 123 عليكم ABC")
        assert "123" in result
        assert "ABC" in result


class TestNormalizeArabicSingleFunctionUsage:
    """Verify same function is used (can be called in both corpus + matching)."""

    def test_function_is_callable_and_pure(self) -> None:
        """normalize_arabic is a pure function."""
        # Same input produces same output every time
        test_text = "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
        result1 = normalize_arabic(test_text)
        result2 = normalize_arabic(test_text)
        assert result1 == result2
        assert result1 is not None
        assert isinstance(result1, str)

    def test_function_can_be_imported_and_called_from_different_contexts(
        self,
    ) -> None:
        """Function can be imported and called for both corpus and STT normalization."""
        # Simulate corpus normalization
        corpus_text = "الْحَمْدُ لِلَّهِ"
        normalized_corpus = normalize_arabic(corpus_text)

        # Simulate STT normalization (user speech with diacritics from STT engine)
        stt_text = "الْحَمْدُ لِلَّهِ"
        normalized_stt = normalize_arabic(stt_text)

        # Both should yield the same normalized form
        assert normalized_corpus == normalized_stt
        assert normalized_corpus == "الحمد لله"

    @pytest.mark.asyncio
    async def test_corpus_uses_same_normalize_function(self) -> None:
        """Verify QuranCorpus uses normalize_arabic in index building."""
        corpus = await get_quran_corpus()

        # Get canonical and normalized texts for a known ayah
        canonical_ayah = corpus.get_ayah(1, 1)
        assert canonical_ayah is not None, "Ayah 1:1 must exist"

        # Get normalized text (built during corpus loading using normalize_arabic)
        normalized_from_corpus = corpus.get_normalized_text(1, 1)
        assert normalized_from_corpus is not None, "Normalized text must be stored"

        # Verify it matches what we'd get by calling normalize_arabic directly
        expected_normalized = normalize_arabic(canonical_ayah.arabic_uthmani)
        assert normalized_from_corpus == expected_normalized, (
            "Corpus must use the same normalize_arabic function"
        )
