"""Qur'an corpus matching engine (MB-016, STAGE 3).

Build inverted n-gram index over normalized corpus for fast candidate lookups.
Match incoming STT window against candidates using token-level similarity scoring.

CRITICAL: All matching happens on normalized text. Rendering uses canonical texts.
The corpus key (surah, ayah) bridges normalized matching ↔ canonical render.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

from mubeen.config import settings
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
    coverage_of_candidate: float = 0.0  # Fraction of candidate ayah covered by window


@dataclass
class MatchWithSecondBest:
    """Match result with second-best score and ambiguity detection."""

    best: Optional[MatchResult]
    second_best_score: float  # Score of runner-up candidate (0.0 if no runner-up)
    is_ambiguous: bool = False  # True if window is valid prefix of multiple candidates
    ambiguous_candidates: list[tuple[int, int]] = field(default_factory=list)  # Other (surah, ayah) sharing window as prefix


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
        """Compute token-level sequence similarity: coverage of window in candidate.

        PRINCIPLED SCORING (not hardcoded penalties):
        Measures: what fraction of the window tokens appear as a contiguous,
        in-order sequence within the candidate, PREFERRING PREFIX MATCHES.

        Scoring strategy:
        - Prefix match (window starts at position 0 of ayah): score = (matched / window_len)
        - Non-prefix substring match: score = 0.5 * (matched / window_len)
          (Recitations typically start at ayah beginning, not middle)
        - Non-contiguous: score low by construction

        This preserves the principle that partial recitations should match highly,
        while still disambiguating when a phrase appears in multiple places.

        Args:
            window_tokens: normalized STT tokens (what was spoken)
            ayah_tokens: normalized ayah tokens (the candidate)

        Returns:
            Similarity in [0.0, 1.0]: weighted by position of match
        """
        window_len = len(window_tokens)
        ayah_len = len(ayah_tokens)

        if window_len == 0:
            return 0.0

        # Find the longest contiguous subsequence of window within ayah
        # Try prefix match first (position 0)
        prefix_matched = 0
        for i in range(window_len):
            if i < ayah_len and ayah_tokens[i] == window_tokens[i]:
                prefix_matched += 1
            else:
                break

        # Try non-prefix matches (starting at position > 0)
        non_prefix_matched = 0
        for start_pos in range(1, ayah_len):
            matched_count = 0
            for i in range(window_len):
                ayah_idx = start_pos + matched_count
                if ayah_idx < ayah_len and ayah_tokens[ayah_idx] == window_tokens[i]:
                    matched_count += 1
                else:
                    break
            non_prefix_matched = max(non_prefix_matched, matched_count)

        # Score: prefer prefix matches, penalize non-prefix by weight from settings
        # (Recitations naturally start at ayah beginning, not middle)
        # Settings: quran_non_prefix_score_weight (default 0.5)
        prefix_score = prefix_matched / window_len
        non_prefix_score = (
            settings.quran_non_prefix_score_weight * non_prefix_matched / window_len
            if non_prefix_matched > 0
            else 0.0
        )

        score = max(prefix_score, non_prefix_score)
        return score

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
        second_best_score = 0.0
        all_candidates_with_scores: list[tuple[int, int, float, str]] = []

        # Score each candidate, track top 2 and all for ambiguity detection
        for surah, ayah in candidates:
            candidate_normalized = self.corpus.get_normalized_text(surah, ayah)
            if not candidate_normalized:
                continue

            candidate_tokens = candidate_normalized.split()
            score = self._token_similarity(window_tokens, candidate_tokens)

            # Calculate coverage of candidate: how much of the candidate ayah does the window cover?
            # This is used to determine if the window is a COMPLETE recitation of a short ayah
            candidate_coverage = len(window_tokens) / len(candidate_tokens) if candidate_tokens else 0.0
            candidate_coverage = min(candidate_coverage, 1.0)  # Cap at 100%

            all_candidates_with_scores.append((surah, ayah, score, candidate_normalized))

            if score > best_score:
                # New best found — old best becomes second-best
                second_best_score = best_score
                best_score = score
                best_result = MatchResult(
                    surah=surah,
                    ayah=ayah,
                    ref_label=f"{surah}:{ayah}",
                    score=score,
                    matched_span=normalized_text,
                    candidate_ayah_normalized=candidate_normalized,
                    coverage_of_candidate=candidate_coverage,
                )
            elif score > second_best_score:
                # Better than second-best but not better than best
                second_best_score = score

        # CRITICAL: Detect ambiguity — when window is a valid prefix of multiple candidates
        # A valid prefix means: window text matches the start of the candidate
        ambiguous_candidates: list[tuple[int, int]] = []
        is_ambiguous = False

        if best_result is not None:
            # Check how many candidates have the window as a valid prefix
            # A valid prefix: normalized text of candidate starts with the window
            candidates_with_prefix = []
            for surah, ayah, score, candidate_normalized in all_candidates_with_scores:
                candidate_words = candidate_normalized.split()
                window_word_count = len(window_tokens)
                # Check if first N words of candidate match the window
                if len(candidate_words) >= window_word_count:
                    candidate_prefix = " ".join(candidate_words[:window_word_count])
                    if candidate_prefix == normalized_text:
                        candidates_with_prefix.append((surah, ayah, score))

            # If multiple candidates share the window as a valid prefix, mark ambiguous
            is_ambiguous = len(candidates_with_prefix) > 1
            if is_ambiguous:
                # List candidates other than the best
                ambiguous_candidates = [
                    (s, a) for s, a, sc in candidates_with_prefix if not (s == best_result.surah and a == best_result.ayah)
                ]
                _log.warning(
                    f"AMBIGUITY DETECTED: Window '{normalized_text}' is valid prefix of "
                    f"{len(candidates_with_prefix)} ayat: {candidates_with_prefix}. "
                    f"Cannot confirm without disambiguation."
                )

        return MatchWithSecondBest(
            best=best_result,
            second_best_score=second_best_score,
            is_ambiguous=is_ambiguous,
            ambiguous_candidates=ambiguous_candidates,
        )


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
