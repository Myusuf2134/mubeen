"""Qur'an corpus matching engine (MB-016, STAGE 3).

Build inverted n-gram index over normalized corpus for fast candidate lookups.
Match incoming STT window against candidates using token-level similarity scoring.

CRITICAL: All matching happens on normalized text. Rendering uses canonical texts.
The corpus key (surah, ayah) bridges normalized matching ↔ canonical render.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from mubeen.services.normalize_arabic import normalize_arabic
from mubeen.services.quran_corpus import AyahData, QuranCorpus, get_quran_corpus

_log = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of matching an STT window against the corpus."""

    surah: int
    ayah: int
    ref_label: str
    score: float  # [0.0, 1.0] token-level similarity
    matched_span: str  # The normalized matched portion
    candidate_ayah_normalized: str  # Full normalized ayah text


class QuranNGramIndex:
    """Inverted n-gram index over normalized Qur'an corpus.

    Maps 3–4 word grams to candidate (surah, ayah) lists.
    Purpose: given a normalized STT window, quickly find candidate ayat
    without scanning all 6,236.
    """

    def __init__(self, n_gram_size: int = 3) -> None:
        """Initialize n-gram index.

        Args:
            n_gram_size: size of word n-grams (3 or 4 recommended).
                        Larger = more specific, fewer candidates.
                        Smaller = more matches, more scoring work.
        """
        self.n_gram_size = n_gram_size
        self.index: dict[tuple[str, ...], set[tuple[int, int]]] = {}
        self._built = False

    async def build_from_corpus(self, corpus: QuranCorpus) -> None:
        """Build the n-gram index from a loaded corpus.

        For each ayah, extract word n-grams from its normalized text,
        and record (surah, ayah) as a candidate for each gram.
        """
        _log.info(f"Building {self.n_gram_size}-gram index over corpus...")

        for ayah_data in corpus.get_all_ayat():
            normalized = corpus.get_normalized_text(ayah_data.surah, ayah_data.ayah)
            if not normalized:
                continue

            # Split into words
            words = normalized.split()
            if len(words) < self.n_gram_size:
                # Too short for n-grams; store as 1-gram for robustness
                for word in words:
                    gram = (word,)
                    if gram not in self.index:
                        self.index[gram] = set()
                    self.index[gram].add((ayah_data.surah, ayah_data.ayah))
            else:
                # Extract n-grams
                for i in range(len(words) - self.n_gram_size + 1):
                    gram = tuple(words[i : i + self.n_gram_size])
                    if gram not in self.index:
                        self.index[gram] = set()
                    self.index[gram].add((ayah_data.surah, ayah_data.ayah))

        self._built = True
        _log.info(f"Built index: {len(self.index)} unique {self.n_gram_size}-grams")

    def query_candidates(self, normalized_window: str) -> set[tuple[int, int]]:
        """Query index for candidate ayat matching the normalized window.

        Strategy: split window into overlapping n-grams, union all matches.
        More specific grams rank higher (fewer matches = higher confidence).

        Args:
            normalized_window: normalized STT text to search

        Returns:
            Set of (surah, ayah) candidate keys
        """
        if not self._built:
            raise RuntimeError("Index not built. Call build_from_corpus() first.")

        if not normalized_window:
            return set()

        words = normalized_window.split()
        if not words:
            return set()

        candidates: set[tuple[int, int]] = set()

        # Extract n-grams from the window
        if len(words) >= self.n_gram_size:
            for i in range(len(words) - self.n_gram_size + 1):
                gram = tuple(words[i : i + self.n_gram_size])
                if gram in self.index:
                    candidates.update(self.index[gram])
        else:
            # Window too short for full n-grams; match on 1-grams
            for word in words:
                gram = (word,)
                if gram in self.index:
                    candidates.update(self.index[gram])

        return candidates


class QuranMatcher:
    """Match STT window against Qur'an corpus using token-level similarity.

    Given normalized text, find the best-matching ayah and return a similarity
    score in [0.0, 1.0]. The score reflects how well the window aligns with
    the candidate's normalized text.
    """

    def __init__(self, n_gram_size: int = 3) -> None:
        self.n_gram_size = n_gram_size
        self.index = QuranNGramIndex(n_gram_size=n_gram_size)
        self.corpus: Optional[QuranCorpus] = None
        self._initialized = False

    async def initialize(self, corpus: Optional[QuranCorpus] = None) -> None:
        """Initialize the matcher with a corpus.

        Args:
            corpus: QuranCorpus instance. If None, uses singleton.
        """
        if corpus is None:
            corpus = await get_quran_corpus()
        self.corpus = corpus
        await self.index.build_from_corpus(corpus)
        self._initialized = True
        _log.info("QuranMatcher initialized")

    def _token_similarity(self, window_tokens: list[str], ayah_tokens: list[str]) -> float:
        """Compute token-level sequence similarity using SequenceMatcher.

        Returns a ratio in [0.0, 1.0] representing how much of the window
        is covered by a contiguous match in the ayah.

        Args:
            window_tokens: normalized STT tokens
            ayah_tokens: normalized ayah tokens

        Returns:
            Similarity in [0.0, 1.0]
        """
        # Use SequenceMatcher to find longest contiguous match
        matcher = SequenceMatcher(None, window_tokens, ayah_tokens)
        # Get ratio: 2 * M / T where M = matches, T = total tokens
        return matcher.ratio()

    async def match(self, normalized_text: str) -> Optional[MatchResult]:
        """Match normalized STT text against corpus.

        Strategy:
        1. Query index for candidate ayat (3–4 word grams)
        2. For each candidate, compute token-level similarity
        3. Return best candidate with score

        Args:
            normalized_text: normalized (diacritics removed, etc.) STT text

        Returns:
            MatchResult with best candidate, score, and matched span.
            Returns None if no candidates found.
        """
        if not self._initialized or not self.corpus:
            raise RuntimeError("Matcher not initialized. Call initialize() first.")

        if not normalized_text:
            return None

        # Query index for candidates
        candidates = self.index.query_candidates(normalized_text)
        if not candidates:
            return None

        window_tokens = normalized_text.split()

        best_score = 0.0
        best_result: Optional[MatchResult] = None

        # Score each candidate
        for surah, ayah in candidates:
            candidate_normalized = self.corpus.get_normalized_text(surah, ayah)
            if not candidate_normalized:
                continue

            candidate_tokens = candidate_normalized.split()
            score = self._token_similarity(window_tokens, candidate_tokens)

            if score > best_score:
                best_score = score
                best_result = MatchResult(
                    surah=surah,
                    ayah=ayah,
                    ref_label=f"{surah}:{ayah}",
                    score=score,
                    matched_span=normalized_text,
                    candidate_ayah_normalized=candidate_normalized,
                )

        return best_result


# Singleton matcher instance
_matcher: Optional[QuranMatcher] = None
_matcher_lock: asyncio.Lock | None = None


async def get_quran_matcher() -> QuranMatcher:
    """Get or initialize the Qur'an matcher (singleton)."""
    global _matcher, _matcher_lock

    if _matcher is None:
        if _matcher_lock is None:
            _matcher_lock = asyncio.Lock()

        async with _matcher_lock:
            if _matcher is None:
                _matcher = QuranMatcher()
                try:
                    await _matcher.initialize()
                except Exception as e:
                    _matcher = None
                    raise

    return _matcher
