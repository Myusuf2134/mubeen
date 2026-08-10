"""Arabic text normalization for Qur'an matching (MB-016, STAGE 2).

Single normalize_arabic() function runs on both:
1. Corpus during index building (STAGE 3)
2. Incoming STT during matching (at render time)

Normalization removes linguistic marks, normalizes character forms, collapses whitespace.
Canonical texts are NEVER normalized — normalization is matching-only.

Per MB-016 brief:
  Strips: all harakat/tanwin/shadda/sukun, tatweel + superscript alif, Quranic
  pause & ayah-end marks; normalizes alif forms (أإآ→ا), ة→ه, ى→ي, hamza-carriers;
  collapses whitespace.
"""

from __future__ import annotations

import re


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for matching.

    The same function is called in both corpus indexing and STT matching.
    Normalization is deterministic and idempotent: calling twice yields the same result.

    CRITICAL: Qur'anic-annotated corpus texts (with wasla, superscript alif, small high marks)
    must normalize to the SAME string as plain STT output. This ensures corpus ayat with
    diacritics match incoming recitation without them.

    Changes:
    - Normalize wasla alif (ٱ U+0671) → base alif (ا)
    - Remove all diacritical marks (harakat, tanwin, shadda, sukun) [U+064B–U+0652]
    - Remove extended marks (U+0653–U+0659: madda, hamza variants, subscript alef)
    - Remove superscript alif (ٰ U+0670) — CRITICAL for Quranic text
    - Remove tatweel (ـــ U+0640)
    - Remove Quranic annotation marks (U+06D6–U+06ED): small high marks, dots, etc.
    - Normalize alif forms (أ → ا, إ → ا, آ → ا)
    - Normalize taa marbuta (ة → ه)
    - Normalize alif maqsura (ى → ي)
    - Normalize hamza carriers (ؤ → و, ئ → ي)
    - Collapse multiple whitespace to single space
    - Strip leading/trailing whitespace

    Args:
        text: Arabic text to normalize (may contain Quranic marks, diacritics, etc.)

    Returns:
        Normalized text with marks/diacritics removed, ready for matching
    """
    if not text:
        return ""

    # Normalize wasla alif (ٱ U+0671) → base alif (ا)
    text = text.replace("ٱ", "ا")

    # Normalize superscript alif (ٰ U+0670) → base alif (ا)
    # The superscript marks an alif in Quranic orthography; convert to full alif
    text = text.replace("ٰ", "ا")

    # Remove diacritical marks: U+064B–U+0652 (fatha, damma, kasra, tanwin, shadda, sukun, etc.)
    text = re.sub(r"[ً-ْ]", "", text)

    # Remove extended marks: U+0653–U+0659 (madda, hamza, subscript alef, etc.)
    text = re.sub(r"[ٓ-ٙ]", "", text)

    # Remove Quranic annotation marks: U+06D6–U+06ED (small high dots, circles, etc.)
    text = re.sub(r"[ۖ-ۭ]", "", text)

    # Normalize alif forms to base alif (ا)
    text = text.replace("أ", "ا")  # أ (alif with hamza above) → ا
    text = text.replace("إ", "ا")  # إ (alif with hamza below) → ا
    text = text.replace("آ", "ا")  # آ (alif with madda) → ا

    # Normalize taa marbuta (ة) to haa (ه)
    text = text.replace("ة", "ه")

    # Normalize alif maqsura (ى) to yaa (ي)
    text = text.replace("ى", "ي")

    # Normalize hamza carriers
    text = text.replace("ؤ", "و")  # ؤ (waw with hamza) → و
    text = text.replace("ئ", "ي")  # ئ (yaa with hamza) → ي

    # Collapse multiple whitespace to single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
