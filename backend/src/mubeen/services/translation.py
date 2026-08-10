"""Translator interface + implementations for sermon machine translation (MB-015).

Transport-neutral streaming contract:
  - translate(text, source_lang, target_lang) -> TranslationResult

Produces finalized TranslationResult objects with machine_generated flag.
CI tests inject FakeTranslator via monkeypatching get_translator() at the
route-module level. OpenAITranslator is used in normal operation.

MB-016 will add is_scripture() corpus matching; until then, all text translates.
"""

from __future__ import annotations

import logging
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

_log = logging.getLogger(__name__)


class TranslationResult(BaseModel):
    """Finalized translation produced by a Translator."""

    model_config = ConfigDict(extra="forbid")

    text: str  # Translated text (target language)
    source_text: str  # Original text (source language)
    machine_generated: bool = True  # Always True for MT (MB-016 will add scripture override)
    source: Literal["machine", "scripture"] = "machine"  # "machine"=MT, "scripture"=corpus


class Translator(Protocol):
    """Transport-neutral machine translation interface."""

    async def translate(
        self,
        text: str,
        source_lang: str = "ar",
        target_lang: str = "en",
    ) -> TranslationResult: ...


class OpenAITranslator:
    """GPT-4o machine translation for Arabic sermons to English (MB-015).

    System prompt enforces: translate Modern Standard / Classical Arabic
    religious sermon speech to natural English; preserve meaning, do not add
    commentary, do not editorialize.

    Usage:
        translator = OpenAITranslator(api_key=settings.openai_api_key)
        result = await translator.translate("السلام عليكم", source_lang="ar", target_lang="en")
    """

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.api_key = api_key
        self.model = model

    async def translate(
        self,
        text: str,
        source_lang: str = "ar",
        target_lang: str = "en",
    ) -> TranslationResult:
        """Translate Arabic sermon text to English using GPT-4o.

        Machine translation is always machine_generated=True.
        MB-016 will add corpus matching and skip scripture text.
        """
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)

        system_prompt = (
            f"You are a translator of Islamic sermons (khutbahs) from {source_lang.upper()} to {target_lang.upper()}. "
            "Translate Modern Standard and Classical Arabic religious sermon speech to natural, idiomatic English. "
            "Preserve all meaning and nuance. Do not add commentary, interpretation, or editorialization. "
            "Respond with only the translation, no explanations or meta-text."
        )

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.3,  # Low temperature for consistency
        )

        translated_text = response.choices[0].message.content.strip()

        return TranslationResult(
            text=translated_text,
            source_text=text,
            machine_generated=True,
            source="machine",
        )


class FakeTranslator:
    """Deterministic fake translator for CI tests.

    Returns prefixed version of input for assertion convenience.
    """

    def __init__(self, prefix: str = "[EN] ") -> None:
        self.prefix = prefix

    async def translate(
        self,
        text: str,
        source_lang: str = "ar",
        target_lang: str = "en",
    ) -> TranslationResult:
        """Return fake translation with recognizable prefix."""
        return TranslationResult(
            text=f"{self.prefix}{text}",
            source_text=text,
            machine_generated=True,
            source="machine",
        )


def is_scripture(text: str) -> bool:
    """Check if text is scripture that should not be machine translated.

    MB-016 will implement corpus matching against Quran/Hadith.
    For now, always return False (all text translates).
    """
    # TODO MB-016: corpus matching against Quranic/Hadith phrases
    return False


def get_translator(api_key: str, model: str = "gpt-4o") -> OpenAITranslator:
    """Factory for OpenAI translator (swappable for tests).

    Tests monkeypatch this at the call site:
        monkeypatch.setattr(
            "mubeen.services.translation.get_translator",
            lambda **_: FakeTranslator()
        )
    """
    return OpenAITranslator(api_key=api_key, model=model)
