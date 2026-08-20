// Hook for TV display WebSocket subscriber — auto-reconnect, heartbeat, liveness.

import { useEffect, useRef, useState, useCallback } from 'react';
import { getWebSocketBase } from '@/utils/websocket';

export interface RenderPayload {
  text: string;
  source_text: string;
  source: 'scripture' | 'machine';
  machine_generated: boolean;
  surah?: number;
  ayah?: number;
  ref_label?: string;
  translation?: string;
  decision_state?: 'CONFIRMED' | 'NEAR_MISS' | 'NOT_SCRIPTURE';
}

export interface BroadcastMessage {
  type: string;
  masjid_id: string;
  sequence_number: number;
  arabic_text: string;
  english_text?: string | null;
  segment_type: string;
  is_partial: boolean;
  render_payload?: RenderPayload | null;
}

export type DisplayState = 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error';

interface UseDisplayWebSocketReturn {
  state: DisplayState;
  history: RenderPayload[];  // Last N finalized captions (newest at end)
  interim: RenderPayload | null;  // Currently forming text (separate from history)
  error: string | null;
}

const _MAX_RECONNECT_ATTEMPTS = 10;
const _RECONNECT_BACKOFF = [1, 2, 4, 8, 16, 32, 32, 32, 32, 32]; // exponential, capped at 32s
const _HISTORY_MAX_SIZE = 6;  // Number of finalized captions to keep on screen

export function useDisplayWebSocket(masjidId: string): UseDisplayWebSocketReturn {
  const [state, setState] = useState<DisplayState>('connecting');
  const [history, setHistory] = useState<RenderPayload[]>([]);  // Finalized captions
  const [interim, setInterim] = useState<RenderPayload | null>(null);  // Currently forming
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Determine WebSocket URL (backend base from VITE_WS_BASE or localhost:8000)
  const getWsUrl = useCallback(() => {
    const base = getWebSocketBase();
    return `${base}/api/khutbah/${masjidId}/live`;
  }, [masjidId]);

  // Clear any pending reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);


  // Handle incoming message
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const msg: BroadcastMessage = {
          type: data.type || 'caption',
          masjid_id: data.masjid_id,
          sequence_number: data.sequence_number,
          arabic_text: data.arabic_text,
          english_text: data.english_text,
          segment_type: data.segment_type || 'plain_speech',
          is_partial: data.is_partial || false,
          render_payload: data.render_payload,
        };

        const payload = msg.render_payload || null;

        if (msg.is_partial) {
          // Interim (forming) text: update the interim state, don't add to history
          setInterim(payload);
        } else {
          // Final text: add to history and clear interim
          if (payload) {
            setHistory((prev) => {
              const newHistory = [...prev, payload];
              // Keep only the last N items
              if (newHistory.length > _HISTORY_MAX_SIZE) {
                newHistory.shift();
              }
              return newHistory;
            });
          }
          setInterim(null);
        }

        setError(null);
      } catch (e) {
        console.error('Display: failed to parse message', e);
        setError('Failed to parse server message');
      }
    },
    []
  );

  // Attempt connection with exponential backoff
  const connect = useCallback(() => {
    const url = getWsUrl();
    console.log(`Display: connecting to ${url} (attempt ${reconnectAttemptRef.current + 1})`);
    setState(reconnectAttemptRef.current > 0 ? 'reconnecting' : 'connecting');

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('Display: WebSocket connected');
        reconnectAttemptRef.current = 0;
        setError(null);
        setState('connected');
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        console.log('Display: WebSocket closed');
        wsRef.current = null;
        if (reconnectAttemptRef.current < _MAX_RECONNECT_ATTEMPTS) {
          const backoff = _RECONNECT_BACKOFF[reconnectAttemptRef.current];
          console.log(`Display: reconnecting in ${backoff}s`);
          reconnectAttemptRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, backoff * 1000);
          setState('reconnecting');
        } else {
          console.error('Display: max reconnect attempts reached');
          setState('disconnected');
          setError('Lost connection to live feed after multiple reconnection attempts');
        }
      };

      ws.onerror = (event) => {
        console.error('Display: WebSocket error', event);
        setState('error');
        setError('Connection error');
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Display: connection failed', e);
      setState('error');
      setError(String(e));
    }
  }, [getWsUrl, handleMessage]);

  // Initial connection on mount
  useEffect(() => {
    connect();
    return () => {
      clearReconnectTimeout();
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect, clearReconnectTimeout]);

  return {
    state,
    history,
    interim,
    error,
  };
}
