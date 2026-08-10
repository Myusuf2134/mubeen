// Hook for TV display WebSocket subscriber — auto-reconnect, heartbeat, liveness.

import { useEffect, useRef, useState, useCallback } from 'react';

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
  message: BroadcastMessage | null;
  payload: RenderPayload | null;
  interim: boolean;
  error: string | null;
}

const _MAX_RECONNECT_ATTEMPTS = 10;
const _RECONNECT_BACKOFF = [1, 2, 4, 8, 16, 32, 32, 32, 32, 32]; // exponential, capped at 32s

export function useDisplayWebSocket(masjidId: string): UseDisplayWebSocketReturn {
  const [state, setState] = useState<DisplayState>('connecting');
  const [message, setMessage] = useState<BroadcastMessage | null>(null);
  const [payload, setPayload] = useState<RenderPayload | null>(null);
  const [interim, setInterim] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Determine WebSocket URL (browser auto-detects http/https → ws/wss)
  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/api/khutbah/${masjidId}/live`;
  }, [masjidId]);

  // Clear any pending reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Clear heartbeat timeout
  const clearHeartbeatTimeout = useCallback(() => {
    if (heartbeatTimeoutRef.current !== null) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  // Setup heartbeat/liveness check (detect silent disconnects)
  const setupHeartbeat = useCallback(() => {
    clearHeartbeatTimeout();
    // If no message arrives in 30 seconds, assume disconnected
    heartbeatTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.warn('Display: heartbeat timeout, closing WebSocket');
        wsRef.current?.close(1000, 'heartbeat_timeout');
      }
    }, 30000);
  }, [clearHeartbeatTimeout]);

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
        setMessage(msg);
        setInterim(msg.is_partial);
        setPayload(msg.render_payload || null);
        setError(null);
        setupHeartbeat();
      } catch (e) {
        console.error('Display: failed to parse message', e);
        setError('Failed to parse server message');
      }
    },
    [setupHeartbeat]
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
        setupHeartbeat();
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        console.log('Display: WebSocket closed');
        clearHeartbeatTimeout();
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
  }, [getWsUrl, handleMessage, setupHeartbeat, clearHeartbeatTimeout]);

  // Initial connection on mount
  useEffect(() => {
    connect();
    return () => {
      clearReconnectTimeout();
      clearHeartbeatTimeout();
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [connect, clearReconnectTimeout, clearHeartbeatTimeout]);

  return {
    state,
    message,
    payload,
    interim,
    error,
  };
}
