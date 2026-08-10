"""Qur'an matching decision logic (MB-016, STAGE 4).

Three-state classification for MatchResult:
- CONFIRMED: score ≥ confirm_threshold, run ≥ min_match_words, margin ≥ min_margin
- NEAR_MISS: passes word/contiguity checks but score/margin is weaker
- NOT_SCRIPTURE: below nearmiss_floor

All thresholds are settings-driven, never hardcoded.
is_scripture(text) returns True ONLY for CONFIRMED.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from mubeen.config import settings
from mubeen.services.quran_matcher import MatchResult, MatchWithSecondBest, get_quran_matcher

_log = logging.getLogger(__name__)


class MatchState(str, Enum):
    """Three possible states for a matched window."""

    CONFIRMED = "CONFIRMED"
    NEAR_MISS = "NEAR_MISS"
    NOT_SCRIPTURE = "NOT_SCRIPTURE"


@dataclass
class DecisionResult:
    """Result of matching decision logic."""

    state: MatchState
    surah: Optional[int] = None
    ayah: Optional[int] = None
    ref_label: Optional[str] = None
    score: Optional[float] = None
    margin: Optional[float] = None  # best_score - second_best_score
    matched_span: Optional[str] = None


class QuranDecision:
    """Apply decision logic to MatchResult, returning three-state classification.

    All thresholds are configurable via settings.
    """

    def __init__(self) -> None:
        self.confirm_threshold = settings.quran_confirm_threshold
        self.nearmiss_floor = settings.quran_nearmiss_floor
        self.min_match_words = settings.quran_min_match_words
        self.min_margin = settings.quran_min_margin

    def decide(self, match_with_second: Optional[MatchWithSecondBest]) -> DecisionResult:
        """Classify a match result into one of three states.

        CRITICAL GUARDS for CONFIRMED:
        1. Score >= confirm_threshold
        2. Word count >= min_match_words
        3. Margin >= min_margin (best - second-best)
        4. Contiguous in-order (enforced in scorer)
        5. NO AMBIGUITY: window must NOT be a valid prefix of multiple ayat

        Args:
            match_with_second: MatchWithSecondBest from matcher (includes ambiguity info)

        Returns:
            DecisionResult with state and details
        """
        # No match found → NOT_SCRIPTURE
        if match_with_second is None or match_with_second.best is None:
            return DecisionResult(state=MatchState.NOT_SCRIPTURE)

        match_result = match_with_second.best
        second_best_score = match_with_second.second_best_score

        # Calculate word count in matched span
        matched_words = len(match_result.matched_span.split()) if match_result.matched_span else 0

        # Calculate margin (best vs second-best) — CRITICAL GUARD
        margin = match_result.score - second_best_score

        _log.debug(
            f"Decision logic for {match_result.ref_label}: "
            f"score={match_result.score:.3f}, words={matched_words}, margin={margin:.3f}, "
            f"ambiguous={match_with_second.is_ambiguous}"
        )

        # CRITICAL DOCTRINAL GUARD: Ambiguity detection
        # If the window is a valid prefix of multiple ayat, we cannot yet know which one
        # the imam is reciting. Must NOT confirm — wait for more text.
        if match_with_second.is_ambiguous:
            _log.warning(
                f"AMBIGUITY GUARD: {match_result.ref_label} matches, but window is also "
                f"valid prefix of {match_with_second.ambiguous_candidates}. "
                f"Cannot confirm without disambiguation. Downgrade to NEAR_MISS."
            )
            # Even if score is high, downgrade to NEAR_MISS due to ambiguity
            return DecisionResult(
                state=MatchState.NEAR_MISS,
                surah=match_result.surah,
                ayah=match_result.ayah,
                ref_label=match_result.ref_label,
                score=match_result.score,
                margin=margin,
                matched_span=match_result.matched_span,
            )

        # Check all CONFIRMED guards (ALL must pass for normal path, OR complete-ayah gate):
        # Normal path:
        # 1. score >= confirm_threshold
        # 2. matched_words >= min_match_words
        # 3. margin >= min_margin (best vs second-best separation)
        # 4. contiguous in-order (enforced in matcher)
        # 5. no ambiguity (checked above)
        #
        # Complete-ayah gate (allows short complete ayat like 112:1):
        # 1. coverage_of_candidate >= complete_ayah_coverage_threshold (e.g., 0.9 = 90%)
        # 2. score >= confirm_threshold
        # 3. margin >= min_margin
        # 4. no ambiguity

        is_complete_ayah = (
            match_result.coverage_of_candidate >= settings.quran_complete_ayah_coverage_threshold
        )

        normal_path_passes = (
            match_result.score >= self.confirm_threshold
            and matched_words >= self.min_match_words
            and margin >= self.min_margin
        )

        complete_ayah_gate_passes = (
            is_complete_ayah
            and match_result.score >= self.confirm_threshold
            and margin >= self.min_margin
        )

        if normal_path_passes or complete_ayah_gate_passes:
            gate_name = "complete-ayah gate" if complete_ayah_gate_passes and not normal_path_passes else "normal path"
            _log.info(
                f"CONFIRMED: {match_result.ref_label} "
                f"(score={match_result.score:.3f}, margin={margin:.3f}, coverage={match_result.coverage_of_candidate:.2f}, gate={gate_name})"
            )
            return DecisionResult(
                state=MatchState.CONFIRMED,
                surah=match_result.surah,
                ayah=match_result.ayah,
                ref_label=match_result.ref_label,
                score=match_result.score,
                margin=margin,
                matched_span=match_result.matched_span,
            )

        # Check NEAR_MISS: word count + contiguity pass, but score/margin is weaker
        if matched_words >= self.min_match_words:
            if (
                match_result.score < self.confirm_threshold
                or margin < self.min_margin
            ):
                _log.warning(
                    f"NEAR_MISS: {match_result.ref_label} "
                    f"(score={match_result.score:.3f}, margin={margin:.3f})"
                )
                return DecisionResult(
                    state=MatchState.NEAR_MISS,
                    surah=match_result.surah,
                    ayah=match_result.ayah,
                    ref_label=match_result.ref_label,
                    score=match_result.score,
                    margin=margin,
                    matched_span=match_result.matched_span,
                )

        # Below nearmiss_floor or below word count → NOT_SCRIPTURE
        if match_result.score < self.nearmiss_floor:
            _log.debug(
                f"NOT_SCRIPTURE: {match_result.ref_label} "
                f"(score={match_result.score:.3f} < {self.nearmiss_floor})"
            )
            return DecisionResult(state=MatchState.NOT_SCRIPTURE)

        # Default: NOT_SCRIPTURE
        return DecisionResult(state=MatchState.NOT_SCRIPTURE)


def is_scripture(text: str) -> bool:
    """Determine if normalized text is canonical scripture (CONFIRMED match).

    This replaces the MB-015 placeholder. Returns True ONLY when:
    - Text matches a Qur'anic ayah with score ≥ confirm_threshold
    - Matched run ≥ min_match_words
    - Margin ≥ min_margin

    Args:
        text: Normalized text to classify

    Returns:
        True if CONFIRMED match (render as scripture), False otherwise
    """
    # Not implemented in STAGE 4 — decision logic only
    # STAGE 5 will wire this into the translation flow
    return False
