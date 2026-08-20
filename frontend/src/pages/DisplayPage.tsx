import { useRef, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useDisplayWebSocket } from '../hooks/useDisplayWebSocket';
import { DisplayRenderer } from '../components/DisplayRenderer';

/**
 * TV display client (MB-017 + MB-018 caption UX rework).
 * Route: /display/:masjidId
 *
 * Display behavior:
 * - The last FINALIZED caption stays on screen, holding its place, until the
 *   next finalized caption is ready to replace it. We deliberately do NOT
 *   render the "interim/transcribing" state on the TV display anymore — the
 *   previous finalized phrase is a better placeholder than a "Transcribing..."
 *   label, since it keeps something readable on screen at all times instead
 *   of flickering to a muted placeholder mid-sentence.
 * - Every finalized caption is still preserved in `history` and viewable
 *   afterward via the "Khutbah so far" panel.
 */
export function DisplayPage() {
  const { masjidId } = useParams<{ masjidId: string }>();
  const [historyOpen, setHistoryOpen] = useState(false);
  const historyScrollRef = useRef<HTMLDivElement>(null);

  if (!masjidId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-emerald-900 via-bg-0 to-bg-1">
        <div className="text-center text-text-2">Invalid masjid ID</div>
      </div>
    );
  }

  const { state: wsState, history, error } = useDisplayWebSocket(masjidId);

  useEffect(() => {
    if (historyOpen && historyScrollRef.current) {
      historyScrollRef.current.scrollTop = historyScrollRef.current.scrollHeight;
    }
  }, [history, historyOpen]);

  const latest = history.length > 0 ? history[history.length - 1] : null;
  const lanHost = import.meta.env.VITE_LAN_HOST as string | undefined;
  const displayUrl = typeof window !== 'undefined'
    ? (lanHost ? `http://${lanHost}:5173${window.location.pathname}` : window.location.href)
    : '';
  const qrSrc = displayUrl
    ? `https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=8&color=247-243-233&bgcolor=12-38-32&data=${encodeURIComponent(displayUrl)}`
    : '';

  return (
    <div className="fixed inset-0 flex flex-col tv-display-background text-ink overflow-hidden">
      {/* Header */}
      <div className="tv-display-header z-50 flex-shrink-0">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="tv-display-header-label">
            <span className="tv-display-header-label">Masjid:</span>{' '}
            <span className="font-mono" style={{ color: '#d4a574' }}>
              {masjidId.slice(0, 8)}
            </span>
          </div>
          <div className="text-center">
            {wsState === 'connected' && (
              <div className="tv-display-header-status">
                <div className="tv-display-header-status-dot" />
                <span>LIVE</span>
              </div>
            )}
            {wsState === 'connecting' && (
              <div className="flex items-center justify-center gap-2">
                <div className="relative w-3 h-3">
                  <div className="absolute inset-0 border border-text-2 rounded-full animate-spin" />
                </div>
                <span className="text-text-2 text-xs uppercase tracking-widest">Connecting...</span>
              </div>
            )}
            {wsState === 'reconnecting' && (
              <div className="flex items-center justify-center gap-2">
                <div className="relative w-3 h-3">
                  <div className="absolute inset-0 border-2 border-transparent border-t-gold border-r-gold rounded-full animate-spin" />
                </div>
                <span className="text-gold text-xs uppercase tracking-widest">Reconnecting...</span>
              </div>
            )}
            {wsState === 'disconnected' && (
              <div className="flex items-center justify-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-red-400 text-xs uppercase tracking-widest">Disconnected</span>
              </div>
            )}
            {wsState === 'error' && (
              <div className="flex items-center justify-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-red-400 text-xs uppercase tracking-widest">Error</span>
              </div>
            )}
          </div>
          <div className="tv-display-header-label">
            {new Date().toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: true,
            })}
          </div>
        </div>
      </div>

      {/* Main content — centered column: caption holds until the next final phrase, then swaps */}
      <div className="flex-1 relative flex flex-col items-center justify-center px-6 py-8 overflow-hidden gap-8">
        {error && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 max-w-md w-full p-4 bg-red-500/10 border border-red-500/30 rounded-lg z-40">
            <div className="text-red-200 text-sm">{error}</div>
            <div className="text-text-2 text-xs mt-2 opacity-60">Auto-reconnecting in background...</div>
          </div>
        )}

        <div className="w-full max-w-4xl text-center">
          <AnimatePresence mode="wait">
            {latest ? (
              <motion.div
                key={`caption-${history.length}`}
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.99 }}
                transition={{ duration: 0.18, ease: 'easeOut' }}
                className="text-white"
              >
                <DisplayRenderer payload={latest} interim={false} masjidName="Mubeen" />
              </motion.div>
            ) : (
              <motion.div
                key="waiting"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="py-16"
              >
                <div style={{ color: 'rgba(212, 165, 116, 0.7)', fontSize: '1rem', marginBottom: '1rem' }}>
                  {wsState === 'connected' ? 'Waiting for khutbah to begin...' : 'Connecting to live feed...'}
                </div>
                {wsState === 'connected' && (
                  <div style={{ color: 'rgba(212, 165, 116, 0.5)', fontSize: '0.75rem' }}>
                    When the khutbah starts, captions will appear here
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* History toggle sits centered, directly below the caption */}
        <button
          onClick={() => setHistoryOpen((v) => !v)}
          className="text-xs px-4 py-2 rounded-full border border-white/15 bg-black/20 backdrop-blur-sm hover:bg-black/30 transition-colors"
          style={{ color: 'rgba(247,243,233,0.75)' }}
        >
          {historyOpen ? 'Close' : 'Khutbah so far'}
        </button>
      </div>

      {/* QR code — pinned to the true viewport bottom-left corner */}
      {qrSrc && (
        <div
          style={{ position: 'fixed', bottom: '4.5rem', left: '1.5rem', zIndex: 40 }}
          className="flex flex-col items-center gap-1.5"
        >
          <div className="bg-black/25 backdrop-blur-sm rounded-lg p-2 border border-white/10">
            <img src={qrSrc} alt="Scan to follow on your phone" width={90} height={90} className="rounded block" />
          </div>
          <span className="text-[10px] tracking-wide" style={{ color: 'rgba(247,243,233,0.55)' }}>
            Scan to follow
          </span>
        </div>
      )}

      {/* Slide-up history panel */}
      <AnimatePresence>
        {historyOpen && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="absolute inset-x-0 bottom-0 z-50 h-[65%] bg-black/70 backdrop-blur-md border-t border-white/10 flex flex-col"
          >
            <div className="flex items-center justify-between px-6 py-3 border-b border-white/10 flex-shrink-0">
              <span className="text-xs uppercase tracking-widest" style={{ color: 'rgba(247,243,233,0.6)' }}>
                Khutbah so far
              </span>
              <button
                onClick={() => setHistoryOpen(false)}
                className="text-xs px-3 py-1.5 rounded-full border border-white/15 hover:bg-white/5"
                style={{ color: 'rgba(247,243,233,0.75)' }}
              >
                Close
              </button>
            </div>
            <div ref={historyScrollRef} className="flex-1 overflow-y-auto caption-scroll-container px-6 py-6 space-y-8">
              {history.length === 0 ? (
                <div className="text-center text-sm" style={{ color: 'rgba(247,243,233,0.4)' }}>
                  Nothing recorded yet.
                </div>
              ) : (
                history.map((payload, idx) => (
                  <div key={`history-${idx}`} className="opacity-90">
                    <DisplayRenderer payload={payload} interim={false} masjidName="Mubeen" />
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="tv-display-footer flex-shrink-0">
        <div className="max-w-6xl mx-auto text-center tv-display-footer-text">
          ⧉ Live khutbah broadcast — Do not edit or interrupt
        </div>
      </div>
    </div>
  );
}
