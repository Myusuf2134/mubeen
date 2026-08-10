# Qur'an Corpus Attribution

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
