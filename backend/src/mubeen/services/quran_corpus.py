"""Qur'an corpus ingestion and storage (MB-016, STAGE 1).

Loads canonical Tanzil Uthmani (Arabic) and Yusuf Ali (English) texts.
Stores byte-for-byte unchanged per Tanzil license requirements.
6,236 ayat (verses), keyed by (surah, ayah).

CRITICAL: Canonical texts are NEVER mutated or normalized for rendering.
Normalization is only for matching (STAGE 2).

Tanzil License Attribution:
  "Quran text obtained from Tanzil Project (www.tanzil.net)
   Tanzil is a Qur'an corpus created by the Tanzil Project"
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from mubeen.services.normalize_arabic import normalize_arabic

_log = logging.getLogger(__name__)


class AyahData(BaseModel):
    """Single Quranic verse (ayah) with canonical texts."""

    surah: int  # 1-114
    ayah: int  # verse number in surah
    arabic_uthmani: str  # Canonical Uthmani text, byte-for-byte unchanged
    yusuf_ali_en: str  # Yusuf Ali translation, unchanged
    surah_name: str  # Arabic surah name
    surah_name_en: str  # English transliteration
    ref_label: str  # e.g. "1:1" or "2:255"


class QuranCorpus:
    """In-memory Qur'an corpus, keyed by (surah, ayah).

    Stores canonical texts and provides lookups. No normalization here —
    normalization is only for matching (STAGE 2).
    """

    TOTAL_AYAT = 6236  # Canonical count

    def __init__(self) -> None:
        self._ayat: dict[tuple[int, int], AyahData] = {}
        self._normalized_texts: dict[tuple[int, int], str] = {}  # Normalized for matching
        self._loaded = False

    async def load_from_tanzil(self) -> None:
        """Load Tanzil Uthmani + Yusuf Ali from bundled JSON files.

        Tanzil provides separate files for each resource:
        - Uthmani: quran-uthmani.json
        - Yusuf Ali: en.yusufali.json
        Both are included in the repo under data/quran/.

        CRITICAL: This method loads FROM FILES IN THE REPO, not from
        external URLs, to ensure byte-for-byte reproducibility and offline operation.
        """
        try:
            # Navigate to repo root: backend/src/mubeen/services/quran_corpus.py → go up 5 levels → data/quran
            data_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "quran"

            if not data_dir.exists():
                raise FileNotFoundError(
                    f"Quran data directory not found at {data_dir}. "
                    f"Download Tanzil v1.1 files from tanzil.net and place in {data_dir}/"
                )

            # Load Uthmani (Arabic)
            uthmani_file = data_dir / "quran-uthmani.json"
            if not uthmani_file.exists():
                raise FileNotFoundError(f"Uthmani file not found: {uthmani_file}")

            _log.info(f"Loading Uthmani from {uthmani_file}")
            with open(uthmani_file, "r", encoding="utf-8") as f:
                uthmani_data = json.load(f)

            # Load Yusuf Ali (English translation)
            yusufali_file = data_dir / "en.yusufali.json"
            if not yusufali_file.exists():
                raise FileNotFoundError(f"Yusuf Ali file not found: {yusufali_file}")

            _log.info(f"Loading Yusuf Ali from {yusufali_file}")
            with open(yusufali_file, "r", encoding="utf-8") as f:
                yusufali_data = json.load(f)

            # Load surah metadata
            surah_file = data_dir / "surah.json"
            if not surah_file.exists():
                raise FileNotFoundError(f"Surah metadata file not found: {surah_file}")

            _log.info(f"Loading surah metadata from {surah_file}")
            with open(surah_file, "r", encoding="utf-8") as f:
                surah_meta = json.load(f)

            # Merge: iterate over Uthmani (authoritative source) and match translations
            for surah_num_str, ayat in uthmani_data.items():
                surah_num = int(surah_num_str)
                surah_info = surah_meta.get(surah_num_str, {})
                surah_name = surah_info.get("name", "")
                surah_name_en = surah_info.get("englishName", "")

                for ayah_num_str, arabic_text in ayat.items():
                    ayah_num = int(ayah_num_str)

                    # Look up English translation
                    english_text = yusufali_data.get(surah_num_str, {}).get(
                        ayah_num_str, ""
                    )

                    ref_label = f"{surah_num}:{ayah_num}"

                    ayah = AyahData(
                        surah=surah_num,
                        ayah=ayah_num,
                        arabic_uthmani=arabic_text,
                        yusuf_ali_en=english_text,
                        surah_name=surah_name,
                        surah_name_en=surah_name_en,
                        ref_label=ref_label,
                    )

                    self._ayat[(surah_num, ayah_num)] = ayah

                    # Build normalized index (same function used in matching)
                    normalized = normalize_arabic(arabic_text)
                    self._normalized_texts[(surah_num, ayah_num)] = normalized

            self._loaded = True
            _log.info(f"quran_corpus_loaded: {len(self._ayat)} ayat")
        except Exception as e:
            _log.error(f"Failed to load Qur'an corpus: {e}")
            raise

    def get_ayah(self, surah: int, ayah: int) -> Optional[AyahData]:
        """Retrieve canonical ayah by surah and ayah number."""
        if not self._loaded:
            raise RuntimeError("Corpus not loaded. Call load_from_tanzil() first.")
        return self._ayat.get((surah, ayah))

    def get_normalized_text(self, surah: int, ayah: int) -> Optional[str]:
        """Retrieve normalized (matching) text for an ayah."""
        if not self._loaded:
            raise RuntimeError("Corpus not loaded. Call load_from_tanzil() first.")
        return self._normalized_texts.get((surah, ayah))

    def get_all_ayat(self) -> list[AyahData]:
        """Return all ayat in order."""
        if not self._loaded:
            raise RuntimeError("Corpus not loaded. Call load_from_tanzil() first.")
        return sorted(self._ayat.values(), key=lambda a: (a.surah, a.ayah))

    def ayat_count(self) -> int:
        """Return count of loaded ayat."""
        return len(self._ayat)

    def is_loaded(self) -> bool:
        """Check if corpus has been loaded."""
        return self._loaded


# Singleton instance
_corpus: Optional[QuranCorpus] = None
_loading_lock: asyncio.Lock | None = None


async def get_quran_corpus() -> QuranCorpus:
    """Get or initialize the Qur'an corpus (singleton)."""
    global _corpus, _loading_lock

    if _corpus is None:
        if _loading_lock is None:
            _loading_lock = asyncio.Lock()

        async with _loading_lock:
            # Double-check after acquiring lock
            if _corpus is None:
                _corpus = QuranCorpus()
                try:
                    await _corpus.load_from_tanzil()
                except Exception as e:
                    _corpus = None  # Reset on failure
                    raise

    return _corpus
