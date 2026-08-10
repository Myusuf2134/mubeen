import { useParams } from 'react-router-dom';
import { useDisplayWebSocket } from '../hooks/useDisplayWebSocket';
import { DisplayRenderer } from '../components/DisplayRenderer';

/**
 * TV display client (MB-017).
 * Route: /display/:masjidId
 *
 * - Persistent WebSocket subscriber to /api/khutbah/{masjidId}/live
 * - Auto-reconnect on network blips (exponential backoff)
 * - Renders MB-016 Stage 5 payload (scripture/machine, final/interim)
 * - LIVE indicator with connection state
 * - Heartbeat/liveness check
 *
 * Design: deep emerald field, gold Amiri Arabic, mint/teal accents.
 * TV-legible type, read from across prayer hall.
 */
export function DisplayPage() {
  const { masjidId } = useParams<{ masjidId: string }>();

  if (!masjidId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-emerald-900 via-bg-0 to-bg-1">
        <div className="text-center text-text-2">Invalid masjid ID</div>
      </div>
    );
  }

  const { state: wsState, payload, interim, error } = useDisplayWebSocket(masjidId);

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-900 via-bg-0 to-bg-1 text-text-0">
      {/* Header with LIVE indicator */}
      <div className="border-b border-surface-bd bg-bg-1/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          {/* Left: Masjid ID */}
          <div className="text-text-1 text-sm opacity-60">
            Masjid: <span className="font-mono text-mint">{masjidId.slice(0, 8)}</span>
          </div>

          {/* Center: Status */}
          <div className="text-center">
            {wsState === 'connected' && (
              <div className="flex items-center justify-center gap-2">
                <div className="relative w-3 h-3">
                  <div className="absolute inset-0 bg-mint rounded-full animate-pulse" />
                  <div className="absolute inset-0.5 bg-mint rounded-full" />
                </div>
                <span className="text-mint font-medium uppercase tracking-widest text-xs">
                  LIVE
                </span>
              </div>
            )}

            {wsState === 'connecting' && (
              <div className="flex items-center justify-center gap-2">
                <div className="relative w-3 h-3">
                  <div className="absolute inset-0 border border-text-2 rounded-full animate-spin" />
                </div>
                <span className="text-text-2 text-xs uppercase tracking-widest">
                  Connecting...
                </span>
              </div>
            )}

            {wsState === 'reconnecting' && (
              <div className="flex items-center justify-center gap-2">
                <div className="relative w-3 h-3">
                  <div className="absolute inset-0 border-2 border-transparent border-t-gold border-r-gold rounded-full animate-spin" />
                </div>
                <span className="text-gold text-xs uppercase tracking-widest">
                  Reconnecting...
                </span>
              </div>
            )}

            {wsState === 'disconnected' && (
              <div className="flex items-center justify-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-red-400 text-xs uppercase tracking-widest">
                  Disconnected
                </span>
              </div>
            )}

            {wsState === 'error' && (
              <div className="flex items-center justify-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-red-400 text-xs uppercase tracking-widest">
                  Error
                </span>
              </div>
            )}
          </div>

          {/* Right: Timestamp */}
          <div className="text-text-1 text-sm opacity-60">
            {new Date().toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: true,
            })}
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex items-center justify-center min-h-[calc(100vh-120px)] px-6 py-8">
        <div className="w-full max-w-4xl">
          {/* Error state */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <div className="text-red-200 text-sm">{error}</div>
              <div className="text-text-2 text-xs mt-2 opacity-60">
                Auto-reconnecting in background...
              </div>
            </div>
          )}

          {/* Display content — render the MB-016 Stage 5 payload */}
          <div className={`transition-opacity duration-300 ${interim ? 'opacity-70' : ''}`}>
            {!payload ? (
              <div className="text-center py-16">
                <div className="text-text-2 text-lg opacity-60 mb-4">
                  {wsState === 'connected'
                    ? 'Waiting for khutbah to begin...'
                    : 'Connecting to live feed...'}
                </div>
                {wsState === 'connected' && (
                  <div className="text-text-2 text-xs opacity-40">
                    When the khutbah starts, captions will appear here
                  </div>
                )}
              </div>
            ) : (
              <DisplayRenderer payload={payload} interim={interim} masjidName="Mubeen" />
            )}
          </div>
        </div>
      </div>

      {/* Footer: indicator that this is a live broadcast */}
      <div className="border-t border-surface-bd bg-bg-1/40 backdrop-blur-sm px-6 py-3">
        <div className="max-w-6xl mx-auto text-center text-text-2 text-xs opacity-50 uppercase tracking-widest">
          ⧉ Live khutbah broadcast — Do not edit or interrupt
        </div>
      </div>
    </div>
  );
}
