import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import type { MasjidSummary } from "@/types/api";

interface Props {
  masjid: MasjidSummary;
  isFavorite: boolean;
  onToggleFavorite: (masjid: MasjidSummary) => void;
  atCapacity: boolean;
}

export function MasjidCard({
  masjid,
  isFavorite,
  onToggleFavorite,
  atCapacity,
}: Props) {
  const canAdd = isFavorite || !atCapacity;

  return (
    <motion.article
      whileHover={{
        y: -3,
        boxShadow: "0 24px 80px rgba(0,0,0,0.50), inset 0 1px 0 rgba(255,255,255,0.10)",
        borderColor: "rgba(94,234,212,0.25)",
        transition: { type: "spring", stiffness: 400, damping: 30 },
      }}
      className="glass rounded-row flex items-center gap-4 p-4"
    >
      {/* Avatar — matches reference .masjid-avatar */}
      <div
        className="h-11 w-11 flex-shrink-0 rounded-icon flex items-center justify-center text-lg"
        style={{
          background:
            "linear-gradient(135deg, rgba(94,234,212,0.20), rgba(212,176,106,0.15))",
        }}
        aria-hidden="true"
      >
        🕌
      </div>

      {/* Name + location */}
      <div className="min-w-0 flex-1">
        <Link
          to={`/masjid/${masjid.id}`}
          className="block truncate font-sora font-semibold text-step-0 text-ink transition-colors duration-150 hover:text-mint focus:outline-none focus-visible:ring-2 focus-visible:ring-mint focus-visible:rounded-sm"
        >
          {masjid.name}
        </Link>
        <p className="mt-0.5 text-step--1 text-ink-muted">
          {masjid.city}, {masjid.state}
        </p>
        {masjid.distance_km != null && (
          <span className="mt-1.5 inline-flex items-center rounded-full border border-mint/20 bg-mint/10 px-2 py-0.5 text-[11px] font-medium text-mint">
            {masjid.distance_km < 1
              ? `${(masjid.distance_km * 1000).toFixed(0)} m`
              : `${masjid.distance_km.toFixed(1)} km`}
          </span>
        )}
      </div>

      {/* Favorite toggle */}
      <motion.button
        type="button"
        whileTap={{ scale: 0.8 }}
        whileHover={{ scale: 1.15 }}
        onClick={() => {
          onToggleFavorite(masjid);
        }}
        disabled={!canAdd}
        aria-label={
          isFavorite
            ? `Remove ${masjid.name} from favorites`
            : `Save ${masjid.name} to favorites`
        }
        aria-pressed={isFavorite}
        title={!canAdd ? "Favorites full (max 5) — remove one to add another" : ""}
        className={[
          "flex-shrink-0 rounded-full p-1.5 transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-mint",
          isFavorite
            ? "text-mint"
            : canAdd
              ? "text-ink-muted hover:text-mint"
              : "cursor-not-allowed text-ink-muted opacity-30",
        ].join(" ")}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill={isFavorite ? "currentColor" : "none"}
          stroke="currentColor"
          strokeWidth={isFavorite ? 0 : 1.5}
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
          />
        </svg>
      </motion.button>
    </motion.article>
  );
}
