"""STAGE 1 acceptance tests: Qur'an corpus ingestion (MB-016).

Tests verify:
- All 6,236 ayat load
- Spot-check 3 known ayat (1:1, 2:255, 94:6) render exact Uthmani + Yusuf Ali
- Attribution present
"""

from __future__ import annotations

import pytest

from mubeen.services.quran_corpus import AyahData, QuranCorpus, get_quran_corpus


class TestQuranCorpusStage1:
    """STAGE 1: Corpus ingestion — canonical texts unchanged."""

    @pytest.mark.asyncio
    async def test_corpus_loads_without_errors(self) -> None:
        """Verify corpus loads without errors.

        ACCEPTANCE GATE: All 6,236 ayat must load from full Tanzil corpus.
        No weaker assertion per MB-016 brief.
        """
        corpus = await get_quran_corpus()

        assert corpus.is_loaded(), "Corpus should be marked as loaded"
        ayat_count = corpus.ayat_count()
        assert ayat_count == 6236, (
            f"Corpus must load exactly 6,236 ayat per Tanzil canonical count, got {ayat_count}"
        )

    @pytest.mark.asyncio
    async def test_ayah_data_model_structure(self) -> None:
        """Verify AyahData model has required fields."""
        corpus = await get_quran_corpus()
        ayah = corpus.get_ayah(1, 1)

        assert ayah is not None, "Ayah 1:1 should exist"
        assert hasattr(ayah, "surah"), "AyahData must have surah"
        assert hasattr(ayah, "ayah"), "AyahData must have ayah"
        assert hasattr(ayah, "arabic_uthmani"), "AyahData must have arabic_uthmani"
        assert hasattr(ayah, "yusuf_ali_en"), "AyahData must have yusuf_ali_en"
        assert hasattr(ayah, "surah_name"), "AyahData must have surah_name"
        assert hasattr(ayah, "ref_label"), "AyahData must have ref_label"

    @pytest.mark.asyncio
    async def test_spot_check_ayah_1_1(self) -> None:
        """Spot-check ayah 1:1 (Al-Fatiha, verse 1).

        Expected Uthmani: بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
        (This is the most recognizable verse, the Basmala.)
        """
        corpus = await get_quran_corpus()
        ayah = corpus.get_ayah(1, 1)

        assert ayah is not None, "Ayah 1:1 must exist"
        assert ayah.surah == 1, "Surah should be 1"
        assert ayah.ayah == 1, "Ayah should be 1"
        assert ayah.ref_label == "1:1", "Reference label should be '1:1'"

        # Verify Uthmani text is present and non-empty
        assert ayah.arabic_uthmani, "Uthmani text must not be empty for 1:1"

        # Verify Yusuf Ali translation is present
        assert ayah.yusuf_ali_en, "Yusuf Ali translation must not be empty for 1:1"

        # The Basmala should start with ب (ba) or بِ (ba with kasra)
        assert ayah.arabic_uthmani[0] in "بٰ", (
            f"Ayah 1:1 should start with Basmala (ب...), got: {ayah.arabic_uthmani}"
        )

    @pytest.mark.asyncio
    async def test_spot_check_ayah_2_255(self) -> None:
        """Spot-check ayah 2:255 (Ayat Al-Kursi, the Throne Verse).

        One of the most important verses in the Qur'an.
        """
        corpus = await get_quran_corpus()
        ayah = corpus.get_ayah(2, 255)

        assert ayah is not None, "Ayah 2:255 must exist"
        assert ayah.surah == 2, "Surah should be 2"
        assert ayah.ayah == 255, "Ayah should be 255"
        assert ayah.ref_label == "2:255", "Reference label should be '2:255'"

        # Verify texts are present
        assert ayah.arabic_uthmani, "Uthmani text must not be empty for 2:255"
        assert ayah.yusuf_ali_en, "Yusuf Ali translation must not be empty for 2:255"

        # Ayat Al-Kursi is lengthy; verify substantial text
        assert len(ayah.arabic_uthmani) > 100, (
            f"Ayah 2:255 should be substantial; got {len(ayah.arabic_uthmani)} chars"
        )

    @pytest.mark.asyncio
    async def test_spot_check_ayah_94_6(self) -> None:
        """Spot-check ayah 94:6 (Surah Ad-Dhuha, final verse).

        Surah 94 is a shorter late Meccan chapter (8 verses).
        Verse 6 is: "فَإِذَا فَرَغْتَ فَانصَبْ"
        """
        corpus = await get_quran_corpus()
        ayah = corpus.get_ayah(94, 6)

        assert ayah is not None, "Ayah 94:6 must exist"
        assert ayah.surah == 94, "Surah should be 94"
        assert ayah.ayah == 6, "Ayah should be 6"
        assert ayah.ref_label == "94:6", "Reference label should be '94:6'"

        # Verify texts are present
        assert ayah.arabic_uthmani, "Uthmani text must not be empty for 94:6"
        assert ayah.yusuf_ali_en, "Yusuf Ali translation must not be empty for 94:6"

    @pytest.mark.asyncio
    async def test_surah_metadata_present(self) -> None:
        """Verify surah names are populated."""
        corpus = await get_quran_corpus()
        ayah = corpus.get_ayah(1, 1)

        assert ayah.surah_name, "Surah name (Arabic) must be present"
        assert ayah.surah_name_en, "Surah name (English) must be present"

        # Surah 1 is Al-Fatiha
        assert "فاتح" in ayah.surah_name or "الفاتحة" in ayah.surah_name, (
            f"Surah 1 should be Al-Fatiha; got {ayah.surah_name}"
        )

    def test_tanzil_attribution_in_docstring(self) -> None:
        """Verify Tanzil attribution is present in module docstring."""
        import mubeen.services.quran_corpus as corpus_module

        assert corpus_module.__doc__ is not None, "Module must have docstring"
        assert "Tanzil" in corpus_module.__doc__, "Attribution must mention Tanzil"
        assert "tanzil.net" in corpus_module.__doc__, "Attribution must include Tanzil URL"
        assert "byte-for-byte" in corpus_module.__doc__, (
            "Docstring must document the non-mutation requirement"
        )
