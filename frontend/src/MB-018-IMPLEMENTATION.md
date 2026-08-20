# MB-018: Browser-based Operator Mic Capture — Implementation Summary

## What was built

### 1. Audio Capture Hook (`useOperatorAudioCapture.ts`)
- **getUserMedia integration**: Requests microphone access with `{ audio: true }`
- **AudioWorkletNode processor**: Pulls raw Float32 samples from the mic stream (not using deprecated ScriptProcessorNode)
- **Audio processing pipeline**:
  - Mic stream is typically 48kHz or 44.1kHz (browser-dependent)
  - Linear interpolation resampler downsamples to 16kHz
  - Float32 PCM samples clamped to [-1, 1] and converted to Int16 PCM (little-endian)
- **WebSocket streaming**: Sends binary Int16 PCM chunks to `wss://host/api/khutbah/{masjidId}/audio?token={operatorJwt}`
- **Connection state management**: Tracks `idle`, `connecting`, `streaming`, `error`, `no-permission` states
- **Cleanup**: Properly closes WebSocket, AudioContext, mic stream, and aborts processor on stop/unmount

### 2. Session API Helpers (`api/sessions.ts`)
- `startSession()`: POST to `/{masjidId}/start` — starts a live session (required before audio capture)
- `stopSession()`: POST to `/{masjidId}/stop` — stops the live session

### 3. Operator Console Page (`pages/OperatorConsolePage.tsx`)
- **JWT decoding**: Extracts `masjid_id` from operator's access token
- **Masjid loading**: Fetches masjid details (name, location)
- **Session control UI**: Start/Stop buttons for live session
- **Audio capture UI**: Mic start/stop controls, visible only when session is active
- **State display**: Shows connection status, errors, and user feedback
- **Sign out**: Logout functionality

### 4. App Routing Update
- Added `/operator` route to `App.tsx` → `OperatorConsolePage`

## Preconditions met

✅ **Live session required**: The audio endpoint (backend/src/mubeen/api/khutbah.py:345) closes with 1008 if no session is active — operator must start a session first.

✅ **Single publisher per masjid**: The endpoint enforces this; the UI shows errors if violated (would be caught server-side).

✅ **Audio format exactly as specified**: linear16 PCM, 16kHz, mono, no container. Resampler and PCM converter follow this spec.

✅ **No MediaRecorder**: Avoided; used AudioWorkletNode + manual resampling + PCM conversion instead.

## What has NOT been verified

❌ **Live mic-to-transcript flow**: I have not:
- Tested actual mic audio input → PCM conversion → WebSocket transmission
- Confirmed Deepgram receives and processes the audio correctly
- Verified that transcripts appear on the TV display in real-time

❌ **Browser compatibility**: 
- AudioWorklet support is modern but not in older browsers (IE11, old Safari)
- getUserMedia is widely supported but requires HTTPS in production

❌ **Audio quality/latency**:
- Sample rate conversion may introduce artifacts (linear interpolation is simple but not optimal)
- Chunk size (2048 samples) and chunking frequency may affect latency
- No testing with real microphone hardware

❌ **Edge cases**:
- Mic permission denied behavior only tested in UI (not live)
- WebSocket disconnection mid-stream recovery untested
- Session expiry while audio is streaming untested

## Known limitations

1. **Resampler quality**: Uses linear interpolation for downsampling. A polyphase or Lanczos resampler would be higher quality, but linear is acceptable for speech.

2. **Chunk buffering**: AudioWorklet processor buffers 2048 samples before sending. This adds ~128ms latency at 16kHz (2048/16000). Could be reduced for lower-latency but higher CPU usage.

3. **No recording**: Does not record audio locally; only streams to backend. For debugging, would need to add local recording via MediaRecorder + WAV export.

## Next steps for verification

1. Start a local dev session: `docker compose up` in backend, `npm run dev` in frontend
2. Navigate to `/operator`, start a session, enable mic capture
3. Speak into the microphone, observe that:
   - Audio capture shows "Streaming" state
   - Backend logs show audio bytes being received
   - Deepgram processes the audio
   - TV display shows live captions appearing
4. Verify WebSocket bytes by adding browser DevTools Network inspection (WebSocket frames)
5. Check browser console for any errors during audio processing
