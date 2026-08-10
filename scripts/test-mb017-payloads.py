#!/usr/bin/env python3
"""
Test script: inject mock MB-016 Stage 5 payloads into the broadcast hub.
Simulates the three render states for MB-017 display testing.

Usage:
  python scripts/test-mb017-payloads.py <masjid_uuid>
"""

import asyncio
import json
import sys
from uuid import UUID, uuid4

sys.path.insert(0, 'backend/src')

from mubeen.services.broadcast import hub
from mubeen.schemas.khutbah import BroadcastMessage, RenderPayloadSchema


async def inject_payloads(masjid_id_str: str) -> None:
    """Inject test payloads into the hub."""
    masjid_id = UUID(masjid_id_str)
    seq = 0

    print(f"Injecting test payloads for masjid {masjid_id}...")
    print()

    # Test 1: Interim state (not final, partial message)
    print("TEST 1: Interim (partial) message...")
    seq += 1
    payload1 = RenderPayloadSchema(
        text="",
        source_text="الحمد لله رب العالمين",
        source="machine",
        machine_generated=True,
        decision_state="NOT_SCRIPTURE",
    )
    msg1 = BroadcastMessage(
        masjid_id=masjid_id,
        sequence_number=seq,
        arabic_text="الحمد لله رب العالمين",
        is_partial=True,
        render_payload=payload1,
    )
    hub.publish(masjid_id, msg1)
    print(f"  Published: seq={seq}, is_partial=True")
    print(f"  Payload: source={payload1.source}, decision_state={payload1.decision_state}")
    await asyncio.sleep(3)
    print()

    # Test 2: Final + CONFIRMED (scripture)
    print("TEST 2: Final (not partial) + CONFIRMED (scripture)...")
    seq += 1
    payload2 = RenderPayloadSchema(
        text="ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَالَمِينَ",  # Actual Uthmani from corpus
        source_text="الحمد لله رب العالمين",
        source="scripture",
        machine_generated=False,
        surah=1,
        ayah=2,
        ref_label="1:2",
        translation="All praise is due to Allah, Lord of all the worlds.",
        decision_state="CONFIRMED",
    )
    msg2 = BroadcastMessage(
        masjid_id=masjid_id,
        sequence_number=seq,
        arabic_text="الحمد لله رب العالمين",
        is_partial=False,
        render_payload=payload2,
    )
    hub.publish(masjid_id, msg2)
    print(f"  Published: seq={seq}, is_partial=False")
    print(f"  Payload: source={payload2.source}, ref_label={payload2.ref_label}, decision_state={payload2.decision_state}")
    print(f"  Arabic (Uthmani): {payload2.text}")
    print(f"  Translation: {payload2.translation}")
    await asyncio.sleep(3)
    print()

    # Test 3: Final + MACHINE (uncertain, NEAR_MISS)
    print("TEST 3: Final + MACHINE (NEAR_MISS)...")
    seq += 1
    payload3 = RenderPayloadSchema(
        text="All praise be to God, the Lord of the worlds.",
        source_text="الحمد لله رب العالمين شيء",  # Slightly off
        source="machine",
        machine_generated=True,
        ref_label="1:2",  # matched, but not confirmed
        decision_state="NEAR_MISS",
    )
    msg3 = BroadcastMessage(
        masjid_id=masjid_id,
        sequence_number=seq,
        arabic_text="الحمد لله رب العالمين شيء",
        is_partial=False,
        render_payload=payload3,
    )
    hub.publish(masjid_id, msg3)
    print(f"  Published: seq={seq}, is_partial=False")
    print(f"  Payload: source={payload3.source}, decision_state={payload3.decision_state}")
    print(f"  Machine text: {payload3.text}")
    await asyncio.sleep(3)
    print()

    # Test 4: Longer complete ayah (2:255 - Ayat al-Kursi)
    print("TEST 4: Final + CONFIRMED (long complete ayah: 2:255)...")
    seq += 1
    payload4 = RenderPayloadSchema(
        text="ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ ٱلۡحَيُّ ٱلۡقَيُّومُۚ لَا تَأۡخُذُهُۥ سِنَةٞ وَلَا نَوۡمٞۚ لَّهُۥ مَا فِي ٱلسَّمَٰوَٰتِ وَمَا فِي ٱلۡأَرۡضِۗ مَن ذَا ٱلَّذِي يَشۡفَعُ عِندَهُۥٓ إِلَّا بِإِذۡنِهِۦۚ يَعۡلَمُ مَا بَيۡنَ أَيۡدِيهِمۡ وَمَا خَلۡفَهُمۡۖ وَلَا يُحِيطُونَ بِشَيۡءٖ مِّنۡ عِلۡمِهِۦٓ إِلَّا بِمَا شَآءَۚ وَسِعَ كُرۡسِيُّهُ ٱلسَّمَٰوَٰتِ وَٱلۡأَرۡضَۖ وَلَا يَـُٔودُهُۥ حِفۡظُهُمَاۚ وَهُوَ ٱلۡعَلِيُّ ٱلۡعَظِيمُ",
        source_text="الله لا الاه الا هو الحي القيوم لا تاخذه سنهٞ ولا نومٞ له ما في السماوات وما في الارض من ذا الذي يشفع عنده الا باذنه يعلم ما بين ايديهم وما خلفهم ولا يحيطون بشيء من علمه الا بما شاء وسع كرسيه السماوات والارض ولا يـوده حفظهما وهو العلي العظيم",
        source="scripture",
        machine_generated=False,
        surah=2,
        ayah=255,
        ref_label="2:255",
        translation="Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence. Neither drowsiness overtakes Him nor sleep. To Him belongs whatever is in the heavens and whatever is on the earth. Who is it that can intercede with Him except by His permission? He knows what is before them and what will be after them, and they encompass not a thing of His knowledge except for what He wills. His Kursi extends over the heavens and the earth, and their preservation tires Him not. And He is the Most High, the Most Great.",
        decision_state="CONFIRMED",
    )
    msg4 = BroadcastMessage(
        masjid_id=masjid_id,
        sequence_number=seq,
        arabic_text="source_text truncated for broadcast",
        is_partial=False,
        render_payload=payload4,
    )
    hub.publish(masjid_id, msg4)
    print(f"  Published: seq={seq}, is_partial=False")
    print(f"  Payload: source={payload4.source}, ref_label={payload4.ref_label}")
    print(f"  (Ayat al-Kursi - 2:255, longest in Quran)")
    await asyncio.sleep(3)
    print()

    print("✓ All test payloads injected. The display should have rendered all three states.")
    print(f"  Open: http://localhost:5173/display/{masjid_id_str}")
    print("  Watch the display render:")
    print("    1. Interim (gray, muted)")
    print("    2. CONFIRMED (gold Amiri Arabic + Yusuf Ali)")
    print("    3. NEAR_MISS (Machine Translation label + English)")
    print("    4. Long CONFIRMED (Ayat al-Kursi)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test-mb017-payloads.py <masjid_uuid>")
        print("Example: python scripts/test-mb017-payloads.py 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)

    masjid_id = sys.argv[1]
    try:
        UUID(masjid_id)
    except ValueError:
        print(f"Invalid UUID: {masjid_id}")
        sys.exit(1)

    asyncio.run(inject_payloads(masjid_id))
