"""Unit tests for Translator interface and implementations (MB-015).

Tests cover: interface contract, machine_generated flag, and integration.
"""

from __future__ import annotations

import pytest

from mubeen.config import settings
from mubeen.services.translation import (
    FakeTranslator,
    OpenAITranslator,
    TranslationResult,
    is_scripture,
)


class TestTranslationResultModel:
    """TranslationResult model contract."""

    def test_translation_result_structure(self) -> None:
        """Verify TranslationResult fields and defaults."""
        result = TranslationResult(
            text="Hello",
            source_text="السلام",
        )

        assert result.text == "Hello"
        assert result.source_text == "السلام"
        assert result.machine_generated is True
        assert result.source == "machine"

    def test_translation_result_forbids_extra_fields(self) -> None:
        """extra='forbid' rejects undeclared fields."""
        with pytest.raises(ValueError):  # Pydantic validation error
            TranslationResult(
                text="Hello",
                source_text="السلام",
                unknown_field="should fail",
            )


class TestFakeTranslator:
    """FakeTranslator for test contracts."""

    @pytest.mark.asyncio
    async def test_fake_translator_basic(self) -> None:
        """FakeTranslator returns recognizable prefixed output."""
        translator = FakeTranslator(prefix="[TEST] ")
        result = await translator.translate("hello", source_lang="ar", target_lang="en")

        assert result.text == "[TEST] hello"
        assert result.source_text == "hello"
        assert result.machine_generated is True
        assert result.source == "machine"

    @pytest.mark.asyncio
    async def test_fake_translator_swappable(self) -> None:
        """FakeTranslator implements Translator protocol."""
        translator = FakeTranslator()

        # Protocol compliance: has translate method with correct signature
        result = await translator.translate(
            text="النص",
            source_lang="ar",
            target_lang="en",
        )

        assert isinstance(result, TranslationResult)
        assert result.machine_generated is True


class TestIsScripture:
    """Scripture detection (MB-016 placeholder)."""

    def test_is_scripture_placeholder_returns_false(self) -> None:
        """Currently always returns False; MB-016 implements corpus matching."""
        # No text is flagged as scripture yet
        assert is_scripture("الحمد لله") is False
        assert is_scripture("من يهده الله") is False
        assert is_scripture("") is False


class TestOpenAITranslator:
    """OpenAI translator (integration test, requires API key)."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not settings.openai_api_key,
        reason="OPENAI_API_KEY not set — skipping live translation test",
    )
    async def test_openai_translator_translates_sermon_text(self) -> None:
        """Live test: GPT-4o translates real sermon phrases to English."""
        translator = OpenAITranslator(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

        # Real sermon phrases from typical khutbahs
        test_phrases = [
            "السلام عليكم ورحمة الله وبركاته",
            "الحمد لله رب العالمين",
            "أشهد أن لا إله إلا الله وأشهد أن محمداً عبده ورسوله",
        ]

        for arabic_text in test_phrases:
            result = await translator.translate(
                text=arabic_text,
                source_lang="ar",
                target_lang=settings.translation_target_lang,
            )

            # Verify result structure
            assert isinstance(result, TranslationResult)
            assert result.text  # Non-empty translation
            assert result.source_text == arabic_text
            assert result.machine_generated is True
            assert result.source == "machine"

            # Sanity: result should be roughly English (no Arabic characters)
            assert not any(ord(c) > 0x064F for c in result.text), (
                f"Translation of '{arabic_text}' should not contain Arabic characters, got: {result.text}"
            )

            # Log translation for inspection
            print(f"\n[MB-015 Translation]\n  AR: {arabic_text}\n  EN: {result.text}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not settings.openai_api_key,
        reason="OPENAI_API_KEY not set — skipping live translation test",
    )
    async def test_openai_translator_machine_generated_always_true(self) -> None:
        """Verify machine_generated is always True (not scripture)."""
        translator = OpenAITranslator(api_key=settings.openai_api_key)

        result = await translator.translate(
            text="الحمد لله رب العالمين",
            source_lang="ar",
            target_lang="en",
        )

        # CRITICAL: machine_generated must always be True for MT
        # MB-016 will override this for corpus-matched scripture
        assert result.machine_generated is True
        assert result.source == "machine"
