# MB-018 Audio Ingest Pipeline Rewiring — Implementation Summary

## What was built

### 1. Enhanced `persist_final_segment()` in `services/khutbah.py`
- Added optional parameters: `english_text`, `quran_surah`, `quran_ayah`
- Now persists enriched segments with translation and scripture references
- Backward compatible: existing calls with just arabic_text still work

### 2. Rewired audio endpoint (`/{masjid_id}/audio` in `api/khutbah.py`)

#### Imports added:
- `PhraseBuffer` from phrase_buffer service
- `is_scripture_with_render()` from quran_render service  
- `get_translator()` from translation service
- `settings` from config
- `RenderPayloadSchema` from schemas

#### New pipeline architecture:

**_result_pump (rewritten):**
- Broadcasts interim results immediately (unchanged behavior for live "forming" text)
- Feeds only finalized results to PhraseBuffer for enrichment

**_enrichment_pump (new concurrent task):**
- Pulls finalized phrases from `buffer.output_queue.get()`
- For each phrase:
  1. Calls `is_scripture_with_render(phrase.text, phrase.text)`
  2. **If scripture matched**: Uses returned `RenderPayload` directly
     - Sets `english_text` from payload.translation
     - Populates `quran_surah` and `quran_ayah`
  3. **If not scripture**: Calls `translator.translate(phrase.text, source_lang="ar", target_lang="en")`
     - Builds `RenderPayload` with `source="machine"`, `machine_generated=True`
     - Sets `english_text` from translation result
     - Leaves `quran_surah`/`quran_ayah` as None
- Broadcasts enriched `BroadcastMessage` with populated `render_payload` and `english_text`
- Persists segment with all enriched fields
- Graceful error handling: catches enrichment exceptions, logs, continues

#### Task management:
- Both `result_task` and `enrichment_task` monitored in `asyncio.wait()`
- Reconnect logic properly cancels and cleans up both tasks
- Drain path on operator disconnect: result_task drains finals, enrichment_task drains buffer

#### Real translator configuration:
- Uses `get_translator(api_key=settings.openai_api_key)` → instantiates `OpenAITranslator`
- NOT using `FakeTranslator`; this is production-ready for real audio

## Exact BroadcastMessage shape (matching text /publish path):
```python
BroadcastMessage(
    type="caption",  # default
    masjid_id=masjid_id,  # UUID from route
    sequence_number=seq,  # server-assigned monotonic
    arabic_text=phrase.text,  # original Arabic
    english_text=<translated or null>,  # NEW: populated by enrichment
    segment_type="plain_speech",  # default
    is_partial=False,  # finals only at this stage
    render_payload=<RenderPayloadSchema>,  # NEW: scripture or machine translation payload
)
```

## What has NOT been verified live

❌ **End-to-end audio → display flow**:
- Real mic audio captured as Int16 PCM
- Audio successfully transmitted over WebSocket to backend
- Deepgram transcribes audio correctly
- Phrases buffered and enriched as expected
- Enriched captions appear on TV display in real-time

❌ **Specific render states observed live**:
- Interim state (gray "Transcribing..." on display)
- Confirmed scripture state (gold Arabic + Yusuf Ali + reference)
- Machine translation state (mint "Machine Translation" label)
- Reconnect scenario (session persists, display continues)

❌ **Edge cases**:
- Deepgram connection drops mid-stream, enrichment pipeline recovers
- Very long phrases or rapid-fire speech buffering behavior
- Translation latency impact on perceived liveness
- Concurrent enrichment task error handling under load
- quran_surah/quran_ayah DB fields actually exist in schema

❌ **Real translator behavior**:
- OpenAI API actually produces reasonable translations
- Translation errors don't break the display

## Notes

1. **PhraseBuffer creates per-session**: Fresh buffer instance for each Deepgram connection attempt. Correct isolation.

2. **Interim broadcast unchanged**: Gray "forming" text still appears immediately via _result_pump broadcast (finals not sent to buffer until enriched).

3. **Sequence number ownership**: Server assigns seq after each enriched final is persisted (unchanged from original).

4. **Error resilience**: Enrichment errors are caught and logged but don't crash the pipeline or drop the WebSocket.

5. **Threading model**: Both _result_pump and _enrichment_pump run concurrently; asyncio ensures serialized access to seq counter via nonlocal.

## Next steps for live verification

1. Start backend, ensure OPENAI_API_KEY is set in environment
2. Start frontend, log in, navigate to `/operator`
3. Start a session, enable mic capture
4. Speak into microphone
5. Watch for:
   - Interim captions in gray (should appear immediately)
   - Final captions enriched with render_payload and english_text
   - Gold scripture rendering if matched, mint machine translation label if not
   - DB khutbah_segments rows populated with english_text and quran fields
