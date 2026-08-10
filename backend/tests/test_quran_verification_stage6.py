"""STAGE 6 verification: must-match and must-NOT-match test sets (MB-016).

The proof that the implementation is doctrinally sound:
- Must-match: known ayat (complete and realistic partials) must ALL CONFIRM
- Must-NOT-match (critical): ordinary speech, common phrases, paraphrases, khutbah
  formulaic Arabic must return NOT_SCRIPTURE or NEAR_MISS — NEVER CONFIRMED

A single CONFIRMED from must-NOT-match set is a doctrinal failure.
"""

from __future__ import annotations

import logging
import pytest

from mubeen.services.quran_corpus import get_quran_corpus
from mubeen.services.quran_decision import MatchState
from mubeen.services.quran_render import is_scripture_with_render

_log = logging.getLogger(__name__)


class TestStage6VerificationMustMatch:
    """Known ayat that MUST all CONFIRM."""

    @pytest.mark.asyncio
    async def test_must_match_complete_short_ayat(self) -> None:
        """Short complete ayat must CONFIRM."""
        corpus = await get_quran_corpus()

        # Short complete ayat (all must CONFIRM when matched in full)
        must_match_refs = [
            (1, 1),      # Basmala (4 words)
            (112, 1),    # Surah Ikhlas: قل هو الله احد (4 words)
            (108, 1),    # Surah Al-Kawthar (2 words)
            (103, 1),    # Surah Al-Asr (3 words)
            (94, 6),     # Ad-Dhuha v6 (5 words)
        ]

        results = []
        for surah, ayah in must_match_refs:
            normalized = corpus.get_normalized_text(surah, ayah)
            assert normalized is not None, f"Ayah {surah}:{ayah} not in corpus"

            is_scripture, payload = await is_scripture_with_render(normalized, normalized)
            ref_label = f"{surah}:{ayah}"
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "ref": ref_label,
                "confirmed": is_scripture,
                "state": state,
            })

            assert is_scripture, (
                f"Must-match {ref_label} failed: expected CONFIRMED, got {state}"
            )

        print("\n=== MUST-MATCH: Short Complete Ayat ===")
        for r in results:
            status = "✓" if r["confirmed"] else "✗"
            print(f"{status} {r['ref']:5} → {r['state'].value}")

    @pytest.mark.asyncio
    async def test_must_match_long_complete_ayat(self) -> None:
        """Long complete ayat must CONFIRM."""
        corpus = await get_quran_corpus()

        must_match_refs = [
            (2, 255),    # Ayat al-Kursi (43 words)
            (2, 152),    # Al-Baqarah v152 (12+ words)
        ]

        results = []
        for surah, ayah in must_match_refs:
            normalized = corpus.get_normalized_text(surah, ayah)
            assert normalized is not None, f"Ayah {surah}:{ayah} not in corpus"

            is_scripture, payload = await is_scripture_with_render(normalized, normalized)
            ref_label = f"{surah}:{ayah}"
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "ref": ref_label,
                "confirmed": is_scripture,
                "state": state,
            })

            assert is_scripture, (
                f"Must-match {ref_label} failed: expected CONFIRMED, got {state}"
            )

        print("\n=== MUST-MATCH: Long Complete Ayat ===")
        for r in results:
            status = "✓" if r["confirmed"] else "✗"
            print(f"{status} {r['ref']:5} → {r['state'].value}")

    @pytest.mark.asyncio
    async def test_must_match_realistic_partials_of_2_255(self) -> None:
        """Realistic 12+ word partials of 2:255 (prefix, past shared opening) must CONFIRM."""
        corpus = await get_quran_corpus()

        ayah_2_255 = corpus.get_normalized_text(2, 255)
        assert ayah_2_255 is not None

        words = ayah_2_255.split()
        assert len(words) >= 43, f"2:255 should have ~43 words, got {len(words)}"

        # Longer prefixes that extend past the shared opening (6-7 words with 3:2)
        # Start from word 0 to avoid non-prefix penalty, go longer to ensure unambiguous
        partial_12_words = " ".join(words[:12])  # words 0-11 (12 words total)
        partial_25_words = " ".join(words[:25])  # words 0-24 (25 words total, middle section)

        results = []
        for partial_text, label in [
            (partial_12_words, "12-word prefix"),
            (partial_25_words, "25-word prefix"),
        ]:
            is_scripture, payload = await is_scripture_with_render(partial_text, partial_text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "label": label,
                "confirmed": is_scripture,
                "state": state,
            })

            assert is_scripture, (
                f"Must-match 2:255 {label} failed: expected CONFIRMED, got {state}"
            )

        print("\n=== MUST-MATCH: Realistic Prefixes of 2:255 ===")
        for r in results:
            status = "✓" if r["confirmed"] else "✗"
            print(f"{status} {r['label']:30} → {r['state'].value}")


class TestStage6VerificationMustNotMatch:
    """Critical doctrinal gate: None of these may CONFIRM."""

    @pytest.mark.asyncio
    async def test_must_not_match_bare_common_phrases(self) -> None:
        """Bare common phrases alone must NOT CONFIRM."""
        must_not_match = [
            ("الحمد لله", "bare praise phrase"),
            ("سبحان الله", "glorification phrase"),
            ("بسم الله", "basmala-like (but not full basmala)"),
            ("لا اله الا الله", "declaration of faith"),
            ("الله اكبر", "takbir"),
            ("استغفر الله", "repentance phrase"),
            ("صلى الله عليه وسلم", "prayer for Prophet"),
        ]

        results = []
        for text, description in must_not_match:
            is_scripture, payload = await is_scripture_with_render(text, text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "text": text,
                "desc": description,
                "confirmed": is_scripture,
                "state": state,
                "ref": payload.ref_label if payload else None,
            })

            assert not is_scripture, (
                f"DOCTRINAL FAILURE: bare phrase '{text}' CONFIRMED as scripture"
            )

        print("\n=== MUST-NOT-MATCH: Bare Common Phrases ===")
        for r in results:
            status = "✓" if not r["confirmed"] else "✗✗✗"
            state_str = r["state"].value if r["state"] else "UNKNOWN"
            print(f"{status} '{r['text']:30}' → {state_str:15} ({r['desc']})")

    @pytest.mark.asyncio
    async def test_must_not_match_khutbah_formulaic(self) -> None:
        """Khutbah formulaic Arabic must NOT CONFIRM."""
        must_not_match = [
            ("ايها الاخوه المسلمون", "O Muslim brothers"),
            ("اتقوا الله حق تقاته", "Fear Allah as He should be feared"),
            ("عباد الله", "O servants of Allah"),
            ("اوصيكم ونفسي بتقوى الله", "I advise you and myself to fear Allah"),
            ("قال الله تعالى", "Allah the Exalted said"),
            ("قال رسول الله", "The Messenger of Allah said"),
        ]

        results = []
        for text, description in must_not_match:
            is_scripture, payload = await is_scripture_with_render(text, text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "text": text,
                "desc": description,
                "confirmed": is_scripture,
                "state": state,
                "ref": payload.ref_label if payload else None,
            })

            assert not is_scripture, (
                f"DOCTRINAL FAILURE: khutbah phrase '{text}' CONFIRMED as scripture"
            )

        print("\n=== MUST-NOT-MATCH: Khutbah Formulaic Arabic ===")
        for r in results:
            status = "✓" if not r["confirmed"] else "✗✗✗"
            state_str = r["state"].value if r["state"] else "UNKNOWN"
            print(f"{status} '{r['text']:45}' → {state_str:15}")

    @pytest.mark.asyncio
    async def test_must_not_match_near_miss_paraphrases(self) -> None:
        """Near-miss paraphrases must NOT CONFIRM."""
        must_not_match = [
            # 94:5 reworded: أَلَمْ نَشْرَحْ لَكَ صَدْرَكَ
            ("الم نوسع لك قلبك", "Reworded 94:5 (نوسع instead of نشرح)"),
            # 2:152 with word substituted: فَاذْكُرُونِي أَذْكُرْكُمْ
            ("فاذكرونا اذكركم", "2:152 with 'نا' instead of 'ني'"),
        ]

        results = []
        for text, description in must_not_match:
            is_scripture, payload = await is_scripture_with_render(text, text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "text": text,
                "desc": description,
                "confirmed": is_scripture,
                "state": state,
                "ref": payload.ref_label if payload else None,
            })

            assert not is_scripture, (
                f"DOCTRINAL FAILURE: paraphrase '{text}' CONFIRMED as scripture"
            )

        print("\n=== MUST-NOT-MATCH: Near-miss Paraphrases ===")
        for r in results:
            status = "✓" if not r["confirmed"] else "✗✗✗"
            state_str = r["state"].value if r["state"] else "UNKNOWN"
            print(f"{status} '{r['text']:35}' → {state_str:15} ({r['desc']})")

    @pytest.mark.asyncio
    async def test_must_not_match_ordinary_modern_arabic(self) -> None:
        """Ordinary modern Arabic must NOT CONFIRM."""
        must_not_match = [
            ("الاجتماع القادم يوم الجمعه بعد صلاه العصر", "Meeting next Friday after Asr prayer"),
            ("نسال الله ان يوفق الجميع", "We ask Allah to grant success to all"),
        ]

        results = []
        for text, description in must_not_match:
            is_scripture, payload = await is_scripture_with_render(text, text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "text": text,
                "desc": description,
                "confirmed": is_scripture,
                "state": state,
                "ref": payload.ref_label if payload else None,
            })

            assert not is_scripture, (
                f"DOCTRINAL FAILURE: modern Arabic '{text}' CONFIRMED as scripture"
            )

        print("\n=== MUST-NOT-MATCH: Ordinary Modern Arabic ===")
        for r in results:
            status = "✓" if not r["confirmed"] else "✗✗✗"
            state_str = r["state"].value if r["state"] else "UNKNOWN"
            print(f"{status} '{r['text']:50}' → {state_str:15}")

    @pytest.mark.asyncio
    async def test_must_not_match_shared_opening_2_255(self) -> None:
        """Shared opening of 2:255 (6-7 words, ambiguous with 3:2) must NOT CONFIRM."""
        corpus = await get_quran_corpus()

        ayah_2_255 = corpus.get_normalized_text(2, 255)
        assert ayah_2_255 is not None

        words = ayah_2_255.split()

        # 6-7 word opening (ambiguous with 3:2)
        partial_6_words = " ".join(words[:6])
        partial_7_words = " ".join(words[:7])

        must_not_match = [
            (partial_6_words, "6-word opening (ambiguous with 3:2)"),
            (partial_7_words, "7-word opening (ambiguous with 3:2)"),
        ]

        results = []
        for text, description in must_not_match:
            is_scripture, payload = await is_scripture_with_render(text, text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            results.append({
                "text": text[:40],  # truncate for display
                "desc": description,
                "confirmed": is_scripture,
                "state": state,
                "ref": payload.ref_label if payload else None,
            })

            assert not is_scripture, (
                f"DOCTRINAL FAILURE: shared opening '{description}' CONFIRMED as scripture"
            )

        print("\n=== MUST-NOT-MATCH: Shared Opening of 2:255 ===")
        for r in results:
            status = "✓" if not r["confirmed"] else "✗✗✗"
            state_str = r["state"].value if r["state"] else "UNKNOWN"
            print(f"{status} {r['desc']:45} → {state_str:15}")


class TestStage6DoctrinalGate:
    """Master test: NO must-NOT item is EVER CONFIRMED."""

    @pytest.mark.asyncio
    async def test_doctrinal_gate_no_false_confirmation(self) -> None:
        """MASTER ASSERTION: Zero false confirmations from must-NOT set.

        This is the core doctrinal requirement. Failing this violates:
        "NEVER render model output (or any uncertain match) as canonical scripture."
        """
        corpus = await get_quran_corpus()

        # All must-NOT items from the spec
        all_must_not = [
            # Bare common phrases (7 items)
            ("الحمد لله", "bare-praise", "bare praise phrase"),
            ("سبحان الله", "bare-glorify", "glorification phrase"),
            ("بسم الله", "bare-basmala", "basmala-like"),
            ("لا اله الا الله", "bare-faith", "declaration of faith"),
            ("الله اكبر", "bare-takbir", "takbir"),
            ("استغفر الله", "bare-repent", "repentance phrase"),
            ("صلى الله عليه وسلم", "bare-prophet", "prayer for Prophet"),

            # Khutbah formulaic (6 items)
            ("ايها الاخوه المسلمون", "khutbah-brothers", "O Muslim brothers"),
            ("اتقوا الله حق تقاته", "khutbah-fear", "Fear Allah as He should"),
            ("عباد الله", "khutbah-servants", "O servants of Allah"),
            ("اوصيكم ونفسي بتقوى الله", "khutbah-advice", "I advise you..."),
            ("قال الله تعالى", "khutbah-allah-said", "Allah said"),
            ("قال رسول الله", "khutbah-prophet-said", "Prophet said"),

            # Near-miss paraphrases (2 items)
            ("الم نوسع لك قلبك", "paraphrase-94-5", "Reworded 94:5"),
            ("فاذكرونا اذكركم", "paraphrase-2-152", "2:152 with substitution"),

            # Modern Arabic (2 items)
            ("الاجتماع القادم يوم الجمعه بعد صلاه العصر", "modern-meeting", "Meeting Friday after Asr"),
            ("نسال الله ان يوفق الجميع", "modern-success", "We ask Allah for success"),
        ]

        # Shared opening of 2:255 (2 items)
        ayah_2_255 = corpus.get_normalized_text(2, 255)
        if ayah_2_255:
            words = ayah_2_255.split()
            all_must_not.append((" ".join(words[:6]), "shared-opening-6w", "6-word opening of 2:255"))
            all_must_not.append((" ".join(words[:7]), "shared-opening-7w", "7-word opening of 2:255"))

        false_confirmations = []
        near_miss_items = []

        # Test each must-NOT item
        print("\n" + "="*100)
        print("STAGE 6 DOCTRINAL GATE: Testing must-NOT items")
        print("="*100 + "\n")

        for text, item_id, description in all_must_not:
            is_scripture, payload = await is_scripture_with_render(text, text)
            state = payload.decision_state if payload else "NO_PAYLOAD"

            if is_scripture:
                false_confirmations.append((text, description, state))
                print(f"✗✗✗ FAIL   '{text[:50]:50}' → {state.value:15} ({description})")
            elif state == MatchState.NEAR_MISS:
                near_miss_items.append({
                    "text": text,
                    "desc": description,
                    "ref": payload.ref_label if payload else None,
                    "score": payload.decision_state,
                })
                print(f"⚠ NEAR_MISS '{text[:50]:50}' → {state.value:15} ({description})")
                if payload and payload.ref_label:
                    print(f"             (Matched to {payload.ref_label})")
            else:
                print(f"✓ PASS     '{text[:50]:50}' → {state.value:15} ({description})")

        # DOCTRINAL GATE: Must have ZERO false confirmations
        assert len(false_confirmations) == 0, (
            f"\n🚨 DOCTRINAL GATE FAILED 🚨\n"
            f"False confirmations: {len(false_confirmations)}\n\n"
            + "\n".join(
                f"  [{i+1}] '{text}' ({desc})"
                for i, (text, desc, state) in enumerate(false_confirmations)
            )
        )

        # Print summary
        print("\n" + "="*100)
        print(f"STAGE 6 RESULT: {len(all_must_not)} must-NOT items tested")
        print(f"  ✓ CONFIRMED: 0/{len(all_must_not)} (PASS)")
        print(f"  ⚠ NEAR_MISS: {len(near_miss_items)} (acceptable, for threshold review)")
        print(f"  ✓ NOT_SCRIPTURE: {len(all_must_not) - len(near_miss_items) - len(false_confirmations)}")
        print("="*100)

        if near_miss_items:
            print("\nNear-miss log (for threshold review):")
            for item in near_miss_items:
                print(f"  - '{item['text']}' matched {item['ref']} ({item['desc']})")

        print("\n✓✓✓ DOCTRINAL GATE PASSED ✓✓✓")
        print("No false confirmations. All guards hold.")
