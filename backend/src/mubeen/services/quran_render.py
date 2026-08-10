"""Qur'an render contract (MB-016, STAGE 5).

Converts decision results into render payloads.
CONFIRMED → canonical Uthmani + Yusuf Ali from corpus (never model output).
NEAR_MISS → machine translation with logging.
NOT_SCRIPTURE → machine translation, no logging.

Wires behind MB-015 is_scripture() seam. MB-015 code unchanged.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, ConfigDict

from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_decision import DecisionResult, MatchState

_log = logging.getLogger(__name__)


class RenderPayload(BaseModel):
    """Payload for rendering matched/translated text. JSON-serializable for broadcast."""

    model_config = ConfigDict(use_enum_values=True)

    text: str  # Text to render (Uthmani for CONFIRMED, translation for others)
    source_text: str  # Original Arabic input
    source: str  # "scripture" or "machine"
    machine_generated: bool  # False for CONFIRMED, True for others
    surah: Optional[int] = None  # For CONFIRMED: surah number
    ayah: Optional[int] = None  # For CONFIRMED: ayah number
    ref_label: Optional[str] = None  # For CONFIRMED: "surah:ayah"
    translation: Optional[str] = None  # For CONFIRMED: Yusuf Ali translation
    decision_state: Optional[str] = None  # For logging (enum value as string)


async def render_from_decision(
    decision: DecisionResult, source_text: str
) -> Optional[RenderPayload]:
    """Convert decision result to render payload per STAGE 5 contract.

    Args:
        decision: DecisionResult from MB-016 decision logic (STAGE 4)
        source_text: Original Arabic STT input

    Returns:
        RenderPayload with source/text/source_text populated.
        Returns None if decision is NOT_SCRIPTURE (no render needed).
    """
    if decision.state == MatchState.CONFIRMED:
        # CRITICAL: Render ONLY canonical corpus text, never model output
        corpus = await get_quran_corpus()
        canonical = corpus.get_ayah(decision.surah, decision.ayah)

        if canonical is None:
            _log.error(
                f"CONFIRMED decision references {decision.ref_label} but ayah not in corpus"
            )
            return None

        payload = RenderPayload(
            text=canonical.arabic_uthmani,  # Canonical Uthmani (byte-for-byte unchanged)
            source_text=source_text,
            source="scripture",
            machine_generated=False,
            surah=decision.surah,
            ayah=decision.ayah,
            ref_label=decision.ref_label,
            translation=canonical.yusuf_ali_en,  # Yusuf Ali translation
            decision_state=MatchState.CONFIRMED,
        )

        _log.info(
            f"CONFIRMED: {decision.ref_label} "
            f"(score={decision.score:.3f}, margin={decision.margin:.3f})"
        )
        return payload

    elif decision.state == MatchState.NEAR_MISS:
        # NEAR_MISS: machine translation path, logged + flagged
        payload = RenderPayload(
            text="",  # Will be filled by MB-015 translator
            source_text=source_text,
            source="machine",
            machine_generated=True,
            ref_label=decision.ref_label,  # For logging: best candidate ref
            decision_state=MatchState.NEAR_MISS,
        )

        _log.warning(
            f"NEAR_MISS: {decision.ref_label} "
            f"(score={decision.score:.3f}, margin={decision.margin:.3f}, window={decision.matched_span})"
        )
        return payload

    else:  # NOT_SCRIPTURE
        # NOT_SCRIPTURE: machine translation path, NOT logged
        payload = RenderPayload(
            text="",  # Will be filled by MB-015 translator
            source_text=source_text,
            source="machine",
            machine_generated=True,
            decision_state=MatchState.NOT_SCRIPTURE,
        )

        # Not logged per contract
        return payload


async def is_scripture_with_render(text: str, source_text: str) -> tuple[bool, Optional[RenderPayload]]:
    """Determine if text is scripture and return render payload.

    This is the MB-016 implementation of is_scripture(), wired behind the
    MB-015 seam. Returns (is_scripture_bool, payload) for caller to decide
    rendering path.

    Args:
        text: Normalized Arabic text to classify
        source_text: Original Arabic input (for logging)

    Returns:
        Tuple of (is_scripture, render_payload).
        - If is_scripture=True: payload contains canonical Uthmani + translation
        - If is_scripture=False: payload contains machine translation instructions
                                 or None for NOT_SCRIPTURE
    """
    from mubeen.services.quran_matcher import get_quran_matcher
    from mubeen.services.quran_decision import QuranDecision

    matcher = await get_quran_matcher()
    decision_engine = QuranDecision()

    # Match: STAGE 3
    match_with_second = await matcher.match(text)

    # Decide: STAGE 4
    decision = decision_engine.decide(match_with_second)

    # Render: STAGE 5
    payload = await render_from_decision(decision, source_text)

    # Return decision + payload
    is_scripture = decision.state == MatchState.CONFIRMED
    return is_scripture, payload
