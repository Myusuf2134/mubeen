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

interface DisplayRendererProps {
  payload: RenderPayload | null;
  interim: boolean;
  masjidName?: string;
}

/**
 * Renders MB-016 Stage 5 payload for TV display.
 *
 * Three states:
 * 1. Interim (not final): gray/muted "forming" state, NEVER as confirmed scripture
 * 2. Final + source="scripture": canonical Arabic (gold, Amiri) + Yusuf Ali + reference
 * 3. Final + source="machine": translation + persistent "Machine translation" label
 */
export function DisplayRenderer({ payload, interim, masjidName }: DisplayRendererProps) {
  // No payload at all
  if (!payload) {
    return (
      <div className="text-center" style={{ color: 'rgba(212, 165, 116, 0.7)', fontSize: '1rem' }}>
        Waiting for live captions...
      </div>
    );
  }

  // State 1: Interim (not final) — ALWAYS muted, NEVER as confirmed scripture
  // Even if source="scripture", interim must NOT render as canonical
  if (interim) {
    return (
      <div className="space-y-4">
        {/* Forming state label */}
        <div style={{ color: 'rgba(212, 165, 116, 0.6)', fontSize: '0.75rem', letterSpacing: '0.08em', textTransform: 'uppercase', fontFamily: 'Sora, sans-serif' }}>
          Transcribing...
        </div>

        {/* Source text (muted, gray) */}
        <div className="caption-arabic" style={{ opacity: 0.75, fontSize: '1.75rem' }}>
          {payload.source_text}
        </div>

        {/* Optional: if there's already a provisional translation, show it gray */}
        {payload.translation && (
          <div className="caption-english" style={{ opacity: 0.65 }}>
            {payload.translation}
          </div>
        )}
      </div>
    );
  }

  // State 2: Final + source="scripture" (CONFIRMED match)
  // Canonical Arabic (Amiri) + Yusuf Ali translation + reference card
  // NEVER show "machine translation" label for scripture
  if (!interim && payload.source === 'scripture' && payload.decision_state === 'CONFIRMED') {
    return (
      <div className="space-y-6">
        {/* Arabic Uthmani (canonical, never model output) */}
        <div className="caption-arabic">
          {payload.text}
        </div>

        {/* Yusuf Ali translation (beneath Arabic, white) */}
        {payload.translation && (
          <div className="caption-english">
            {payload.translation}
          </div>
        )}

        {/* Scripture reference citation */}
        {payload.ref_label && (
          <div className="scripture-citation">
            {payload.ref_label}
            {payload.surah && payload.ayah && (
              <span className="ml-2">
                • Surah {payload.surah}, Verse {payload.ayah}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }

  // State 3: Final + source="machine" (NEAR_MISS or NOT_SCRIPTURE)
  // Translation with PERSISTENT, non-dismissible "Machine translation" label
  if (!interim && (payload.source === 'machine' || (payload.source === 'scripture' && payload.decision_state !== 'CONFIRMED'))) {
    return (
      <div className="space-y-6">
        {/* Original Arabic (gray, smaller, for context) */}
        {payload.source_text && (
          <div className="caption-arabic" style={{ opacity: 0.7, fontSize: '1.5rem' }}>
            {payload.source_text}
          </div>
        )}

        {/* Translated text (prominent, white/silver) */}
        {payload.text && (
          <div className="caption-english">
            {payload.text}
          </div>
        )}
      </div>
    );
  }

  // Fallback (should not reach here if payload is well-formed)
  return (
    <div style={{ color: 'rgba(212, 165, 116, 0.6)', fontSize: '0.875rem' }}>
      <div>Unknown render state</div>
      {payload.source_text && (
        <div style={{ fontSize: '1rem', marginTop: '1rem', opacity: 0.5 }}>
          {payload.source_text}
        </div>
      )}
    </div>
  );
}
