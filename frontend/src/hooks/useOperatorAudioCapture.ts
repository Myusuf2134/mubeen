// Hook for operator mic capture → WebSocket audio streaming (linear16 PCM, 16kHz, mono).
// Handles: getUserMedia → AudioWorkletNode → resample to 16kHz → Float32→Int16 PCM → binary WS.

import { useEffect, useRef, useState, useCallback } from 'react';
import { getWebSocketBase } from '@/utils/websocket';

export type AudioCaptureState = 'idle' | 'connecting' | 'streaming' | 'error' | 'no-permission';

interface UseOperatorAudioCaptureReturn {
  state: AudioCaptureState;
  error: string | null;
  startCapture: () => Promise<void>;
  stopCapture: () => void;
  isCapturing: boolean;
}

// AudioWorklet processor: pulls raw Float32 samples from mic stream.
const AUDIO_PROCESSOR_CODE = `
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = [];
  }

  process(inputs, outputs) {
    const input = inputs[0];
    if (input && input.length > 0) {
      const channelData = input[0];
      for (let i = 0; i < channelData.length; i++) {
        this.buffer.push(channelData[i]);
      }
      // Send chunks of 2048 samples at a time to keep memory usage low.
      if (this.buffer.length >= 2048) {
        this.port.postMessage({ type: 'audio', samples: this.buffer });
        this.buffer = [];
      }
    }
    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);
`;

export function useOperatorAudioCapture(
  masjidId: string,
  operatorJwt: string,
  sessionActive: boolean,
): UseOperatorAudioCaptureReturn {
  const [state, setState] = useState<AudioCaptureState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const processorAbortRef = useRef<AbortController | null>(null);

  // Resample Float32 samples from mic (typically 48kHz) to 16kHz.
  // Simple linear interpolation resampler.
  const resampleTo16k = useCallback((samples: Float32Array, inputSampleRate: number): Float32Array => {
    const targetSampleRate = 16000;
    const ratio = targetSampleRate / inputSampleRate;
    const targetLength = Math.ceil(samples.length * ratio);
    const resampled = new Float32Array(targetLength);

    for (let i = 0; i < targetLength; i++) {
      const srcIndex = i / ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, samples.length - 1);
      const frac = srcIndex - srcIndexFloor;

      // Linear interpolation
      resampled[i] =
        samples[srcIndexFloor] * (1 - frac) + samples[srcIndexCeil] * frac;
    }

    return resampled;
  }, []);

  // Convert Float32 PCM to Int16 PCM (little-endian).
  const float32ToInt16 = useCallback((float32: Float32Array): Uint8Array => {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      // Clamp to [-1, 1]
      const s = Math.max(-1, Math.min(1, float32[i]));
      // Convert to Int16
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return new Uint8Array(int16.buffer);
  }, []);

  const stopCapture = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (processorAbortRef.current) {
      processorAbortRef.current.abort();
      processorAbortRef.current = null;
    }
    setIsCapturing(false);
    setState('idle');
  }, []);

  const startCapture = useCallback(async () => {
    if (!sessionActive) {
      setError('No active session. Start a session first.');
      setState('error');
      return;
    }

    if (isCapturing) return;

    setError(null);
    setState('connecting');

    try {
      // 1. Request mic access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      // 2. Create AudioContext (use mic's native sample rate)
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const inputSampleRate = audioContext.sampleRate;

      // 3. Create and load AudioWorklet processor
      const blob = new Blob([AUDIO_PROCESSOR_CODE], { type: 'application/javascript' });
      const workletUrl = URL.createObjectURL(blob);
      await audioContext.audioWorklet.addModule(workletUrl);

      // 4. Create AudioWorkletNode and connect mic to it
      const workletNode = new AudioWorkletNode(audioContext, 'audio-processor');
      workletNodeRef.current = workletNode;
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(workletNode);
      // Zero-gain node keeps audio graph active (so process() fires) without mic audio being audible.
      const silenceNode = audioContext.createGain();
      silenceNode.gain.value = 0;
      workletNode.connect(silenceNode);
      silenceNode.connect(audioContext.destination);

      // 5. Open WebSocket to audio endpoint
      const base = getWebSocketBase();
      const wsUrl = `${base}/api/khutbah/${masjidId}/audio?token=${operatorJwt}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Operator: audio WebSocket connected');
        setState('streaming');
        setIsCapturing(true);
        setError(null);
      };

      ws.onerror = (event) => {
        console.error('Operator: audio WebSocket error', event);
        setState('error');
        setError('WebSocket connection failed');
        stopCapture();
      };

      ws.onclose = () => {
        console.log('Operator: audio WebSocket closed');
        stopCapture();
      };

      // 6. Listen to audio processor messages and forward to WebSocket
      processorAbortRef.current = new AbortController();
      const signal = processorAbortRef.current.signal;

      workletNode.port.onmessage = (event) => {
        if (signal.aborted) return;
        if (event.data.type === 'audio' && ws.readyState === WebSocket.OPEN) {
          try {
            // Resample from mic's native rate to 16kHz
            const samples = new Float32Array(event.data.samples);
            const resampled = resampleTo16k(samples, inputSampleRate);

            // Convert Float32 to Int16 PCM
            const pcm = float32ToInt16(resampled);

            // Send binary chunk to backend
            ws.send(pcm);
          } catch (e) {
            console.error('Operator: audio processing error', e);
            setError('Failed to process audio');
            setState('error');
            stopCapture();
          }
        }
      };
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      console.error('Operator: capture startup failed', e);

      if (errMsg.includes('NotAllowedError') || errMsg.includes('Permission denied')) {
        setState('no-permission');
        setError('Microphone permission denied. Please allow mic access in browser settings.');
      } else {
        setState('error');
        setError(`Failed to start audio capture: ${errMsg}`);
      }

      stopCapture();
    }
  }, [masjidId, operatorJwt, sessionActive, isCapturing, resampleTo16k, float32ToInt16, stopCapture]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCapture();
    };
  }, [stopCapture]);

  return {
    state,
    error,
    startCapture,
    stopCapture,
    isCapturing,
  };
}
