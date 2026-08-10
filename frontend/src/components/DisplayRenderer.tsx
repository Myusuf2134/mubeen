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
      <div className="text-center text-text-2 text-lg">
        Waiting for live captions...
      </div>
    );
  }

  // State 1: Interim (not final) — ALWAYS muted, NEVER as confirmed scripture
  // Even if source="scripture", interim must NOT render as canonical
  if (interim) {
    return (
      <div className="space-y-4 animate-pulse">
        {/* Forming state label */}
        <div className="text-text-2 text-sm font-medium tracking-widest uppercase opacity-60">
          Transcribing...
        </div>

        {/* Source text (muted, gray) */}
        <div className="text-text-2 text-2xl leading-relaxed font-serif opacity-60">
          {payload.source_text}
        </div>

        {/* Optional: if there's already a provisional translation, show it gray */}
        {payload.translation && (
          <div className="text-text-2 text-sm opacity-40 italic">
            {payload.translation}
          </div>
        )}
      </div>
    );
  }

  // State 2: Final + source="scripture" (CONFIRMED match)
  // Canonical Arabic (Amiri) + Yusuf Ali translation + reference card
  // NEVER show "machine translation" label for scripture
  if (!interim && payload.source === 'scripture') {
    return (
      <div className="space-y-8">
        {/* Reference card (surah:ayah + surah name) */}
        {payload.ref_label && (
          <div className="flex items-start justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-1 h-10 bg-gold rounded-full" />
              <div>
                <div className="text-gold font-bold text-lg tracking-wider uppercase">
                  {payload.ref_label}
                </div>
                {payload.surah && payload.ayah && (
                  <div className="text-text-2 text-xs opacity-60 mt-1">
                    Surah {payload.surah}, Verse {payload.ayah}
                  </div>
                )}
              </div>
            </div>
            {masjidName && (
              <div className="text-text-2 text-xs opacity-50 uppercase tracking-widest whitespace-nowrap">
                {masjidName}
              </div>
            )}
          </div>
        )}

        {/* Arabic Uthmani (canonical, never model output) — prominent, gold, right-aligned */}
        <div className="text-right">
          <div className="text-gold text-5xl leading-loose font-serif">
            {payload.text}
          </div>
        </div>

        {/* Yusuf Ali translation (beneath Arabic, silver/white) */}
        {payload.translation && (
          <div className="pt-6 border-t border-surface-bd">
            <div className="text-text-0 text-2xl leading-relaxed">
              {payload.translation}
            </div>
          </div>
        )}

        {/* Settle animation */}
        <style>{`
          @keyframes settle {
            from {
              opacity: 0.8;
              filter: blur(0.5px);
            }
            to {
              opacity: 1;
              filter: blur(0);
            }
          }
          .scripture-render {
            animation: settle 0.6s ease-out forwards;
          }
        `}</style>
        <div className="scripture-render" />
      </div>
    );
  }

  // State 3: Final + source="machine" (NEAR_MISS or NOT_SCRIPTURE)
  // Translation with PERSISTENT, non-dismissible "Machine translation" label
  if (!interim && payload.source === 'machine') {
    return (
      <div className="space-y-6">
        {/* Persistent "Machine translation" banner (non-dismissible) */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-mint/40 bg-mint/5">
          <div className="w-2 h-2 bg-mint rounded-full animate-pulse" />
          <span className="text-mint text-xs font-bold uppercase tracking-widest">
            Machine Translation
          </span>
        </div>

        {/* Original Arabic (gray, smaller, for context) */}
        {payload.source_text && (
          <div className="text-text-2 text-lg opacity-60 font-serif">
            {payload.source_text}
          </div>
        )}

        {/* Translated text (prominent, white/silver) */}
        {payload.text && (
          <div className="text-text-0 text-3xl leading-relaxed">
            {payload.text}
          </div>
        )}
      </div>
    );
  }

  // Fallback (should not reach here if payload is well-formed)
  return (
    <div className="text-text-2 text-sm">
      <div className="opacity-60">Unknown render state</div>
      {payload.source_text && (
        <div className="text-lg mt-4 opacity-40">{payload.source_text}</div>
      )}
    </div>
  );
}
