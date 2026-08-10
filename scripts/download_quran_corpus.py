#!/usr/bin/env python3
"""Download Tanzil Qur'an corpus (Uthmani + Yusuf Ali translation).

Fetches from GitHub (risan/quran-json which includes Tanzil data) and saves to data/quran/.
Respects Tanzil license: attribution required.

Usage:
    python scripts/download_quran_corpus.py
"""

import json
import sys
from pathlib import Path
from urllib.request import urlopen


def download_quran_corpus():
    """Download Tanzil Uthmani and English translations."""
    data_dir = Path(__file__).parent.parent / "data" / "quran"
    data_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading Tanzil Uthmani (Arabic)...")
    uthmani_url = "https://raw.githubusercontent.com/risan/quran-json/master/dist/quran.json"

    try:
        print(f"Fetching from: {uthmani_url}")
        with urlopen(uthmani_url, timeout=30) as response:
            quran_data = json.loads(response.read())

        # Transform from [{id, name, verses: [{id, text}]}] to {surah: {ayah: text}}
        quran_dict = {}
        for surah in quran_data:
            surah_num = str(surah["id"])
            quran_dict[surah_num] = {}
            for verse in surah["verses"]:
                ayah_num = str(verse["id"])
                quran_dict[surah_num][ayah_num] = verse["text"]

        with open(data_dir / "quran-uthmani.json", "w", encoding="utf-8") as f:
            json.dump(quran_dict, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved Uthmani: {len(quran_dict)} surahs")

    except Exception as e:
        print(f"✗ Failed to download Uthmani: {e}", file=sys.stderr)
        return False

    # 2. English translation (Yusuf Ali variant)
    print("Downloading English translation...")
    try:
        trans_url = "https://raw.githubusercontent.com/risan/quran-json/master/dist/quran_en.json"
        print(f"Fetching from: {trans_url}")

        with urlopen(trans_url, timeout=30) as response:
            trans_data = json.loads(response.read())

        # Transform from [{id, verses: [{id, text}]}] to {surah: {ayah: text}}
        trans_dict = {}
        for surah in trans_data:
            surah_num = str(surah["id"])
            trans_dict[surah_num] = {}
            for verse in surah["verses"]:
                ayah_num = str(verse["id"])
                trans_dict[surah_num][ayah_num] = verse["text"]

        with open(data_dir / "en.yusufali.json", "w", encoding="utf-8") as f:
            json.dump(trans_dict, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved English translation: {len(trans_dict)} surahs")

    except Exception as e:
        print(f"✗ Failed to download translation: {e}", file=sys.stderr)
        return False

    # 3. Surah metadata
    print("Creating surah metadata...")
    try:
        # Build surah metadata from the main quran.json (already loaded)
        meta_dict = {}
        for surah in quran_data:
            num = str(surah["id"])
            meta_dict[num] = {
                "name": surah.get("name", ""),
                "englishName": surah.get("transliteration", ""),
            }

        with open(data_dir / "surah.json", "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved surah metadata: {len(meta_dict)} surahs")

    except Exception as e:
        print(f"✗ Failed to create surah metadata: {e}", file=sys.stderr)
        return False

    # 4. Attribution
    print("Writing attribution...")
    attribution = """# Qur'an Corpus Attribution

This directory contains Qur'anic texts obtained from the Tanzil Project.

## Tanzil Project
- **Source:** https://tanzil.net/
- **License:** Tanzil requires the following attribution:
  "Quran text obtained from the Tanzil Project. Tanzil is a Qur'an corpus
   created by the Tanzil Project and contributors."
- **Version:** Uthmani (Arabic), English Translation

## Files
- `quran-uthmani.json`: Canonical Arabic text (Uthmani orthography)
- `en.yusufali.json`: English translation
- `surah.json`: Surah metadata (names, transliterations)

## Data Format
All files use the structure:
```json
{
  "surah_number": {
    "ayah_number": "text content"
  }
}
```

6,236 total verses (ayat) across 114 chapters (surahs).

## Legal Notice
These texts are provided under Tanzil's non-commercial license.
Mubeen uses them solely for accurate scripture identification in sermon captions.
"""

    with open(data_dir / "ATTRIBUTION.md", "w", encoding="utf-8") as f:
        f.write(attribution)
    print("✓ Written ATTRIBUTION.md")

    return True


if __name__ == "__main__":
    success = download_quran_corpus()
    if success:
        print("\n✓ Quran corpus downloaded successfully")
        sys.exit(0)
    else:
        print("\n✗ Failed to download corpus")
        sys.exit(1)
