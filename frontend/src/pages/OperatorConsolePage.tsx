import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { getMasjid } from '@/api/masjids';
import { startSession, stopSession } from '@/api/sessions';
import { useOperatorAudioCapture } from '@/hooks/useOperatorAudioCapture';
import type { MasjidDetail } from '@/types/api';

function decodeJWTMasjidId(token: string): string | null {
  try {
    const b64url = token.split('.')[1] ?? '';
    const b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
    const padded = b64.padEnd(b64.length + ((4 - (b64.length % 4)) % 4), '=');
    const payload = JSON.parse(atob(padded)) as Record<string, unknown>;
    return typeof payload.masjid_id === 'string' ? payload.masjid_id : null;
  } catch {
    return null;
  }
}

export function OperatorConsolePage() {
  const navigate = useNavigate();
  const { token, clearToken } = useAuth();

  const [masjid, setMasjid] = useState<MasjidDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionActive, setSessionActive] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const masjidId = token ? decodeJWTMasjidId(token) : null;

  // Audio capture hook
  const audio = useOperatorAudioCapture(masjidId || '', token || '', sessionActive);

  // Load masjid details on mount
  useEffect(() => {
    if (!token || !masjidId) {
      clearToken();
      navigate('/login');
      return;
    }

    setLoading(true);
    getMasjid(masjidId)
      .then(setMasjid)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load masjid');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token, masjidId, clearToken, navigate]);

  const handleStartSession = async () => {
    if (!token || !masjidId) return;
    setSessionLoading(true);
    setError(null);

    try {
      await startSession(masjidId, token);
      setSessionActive(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session');
    } finally {
      setSessionLoading(false);
    }
  };

  const handleStopSession = async () => {
    if (!token || !masjidId) return;
    setSessionLoading(true);
    setError(null);

    try {
      await stopSession(masjidId, token);
      setSessionActive(false);
      audio.stopCapture();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop session');
    } finally {
      setSessionLoading(false);
    }
  };

  const handleStartAudio = async () => {
    try {
      await audio.startCapture();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start audio capture');
    }
  };

  if (!token || !masjidId) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16 text-center">
        <p className="text-ink-muted">Redirecting to login...</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16 text-center">
        <p className="text-ink-muted">Loading console...</p>
      </div>
    );
  }

  if (!masjid) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16 text-center">
        <p className="text-red-400">Failed to load masjid</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-5 py-8">
      <h1 className="text-3xl font-bold mb-2">{masjid.name}</h1>
      <p className="text-ink-muted mb-8">{masjid.city}, {masjid.state}</p>

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-400/10 border border-red-400/25 rounded-lg">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Session control */}
      <div className="mb-8 p-6 bg-raised rounded-lg border border-surface-bd">
        <h2 className="text-lg font-semibold mb-4">Live Session</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <p className="text-sm text-ink-muted">
              Status: <span className={sessionActive ? 'text-mint' : 'text-ink-dim'}>
                {sessionActive ? 'Active' : 'Inactive'}
              </span>
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleStartSession}
              disabled={sessionActive || sessionLoading}
              className="px-4 py-2 bg-mint text-background rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-mint/90 transition"
            >
              {sessionLoading ? 'Starting...' : 'Start'}
            </button>
            <button
              onClick={handleStopSession}
              disabled={!sessionActive || sessionLoading}
              className="px-4 py-2 bg-red-500/20 text-red-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-500/30 transition"
            >
              {sessionLoading ? 'Stopping...' : 'Stop'}
            </button>
          </div>
        </div>
      </div>

      {/* Audio capture control */}
      {sessionActive && (
        <div className="p-6 bg-raised rounded-lg border border-surface-bd">
          <h2 className="text-lg font-semibold mb-4">Operator Microphone</h2>

          {/* Connection state */}
          <div className="mb-4 p-3 bg-surface-bg rounded">
            <p className="text-sm text-ink-muted">
              Status: <span className={`font-medium ${
                audio.state === 'streaming' ? 'text-mint' :
                audio.state === 'connecting' ? 'text-yellow-400' :
                audio.state === 'no-permission' ? 'text-red-400' :
                audio.state === 'error' ? 'text-red-400' :
                'text-ink-dim'
              }`}>
                {audio.state === 'idle' ? 'Ready' :
                 audio.state === 'connecting' ? 'Connecting...' :
                 audio.state === 'streaming' ? 'Streaming' :
                 audio.state === 'error' ? 'Error' :
                 audio.state === 'no-permission' ? 'No Permission' :
                 audio.state}
              </span>
            </p>
          </div>

          {/* Error message */}
          {audio.error && (
            <div className="mb-4 p-3 bg-red-400/10 border border-red-400/25 rounded text-red-300 text-sm">
              {audio.error}
            </div>
          )}

          {/* Start/Stop audio buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleStartAudio}
              disabled={audio.isCapturing}
              className="px-4 py-2 bg-mint text-background rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-mint/90 transition"
            >
              {audio.isCapturing ? 'Capturing...' : 'Start Mic'}
            </button>
            <button
              onClick={audio.stopCapture}
              disabled={!audio.isCapturing}
              className="px-4 py-2 bg-red-500/20 text-red-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-500/30 transition"
            >
              Stop Mic
            </button>
          </div>
        </div>
      )}

      {!sessionActive && (
        <div className="p-6 bg-surface-bg rounded-lg border border-surface-bd text-center text-ink-muted">
          <p>Start a session to enable audio capture.</p>
        </div>
      )}

      {/* Sign out */}
      <div className="mt-8 pt-8 border-t border-surface-bd">
        <button
          onClick={() => {
            clearToken();
            navigate('/');
          }}
          className="text-sm text-ink-muted hover:text-ink-dim transition"
        >
          ← Sign out
        </button>
      </div>
    </div>
  );
}
