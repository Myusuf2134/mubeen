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
    <article className="flex items-start justify-between rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="min-w-0 flex-1">
        <Link
          to={`/masjid/${masjid.id}`}
          className="block truncate text-base font-semibold text-gray-900 hover:text-emerald-700 focus:outline-none focus-visible:underline"
        >
          {masjid.name}
        </Link>
        <p className="mt-0.5 text-sm text-gray-500">
          {masjid.city}, {masjid.state}
        </p>
        {masjid.distance_km != null && (
          <p className="mt-0.5 text-xs text-gray-400">
            {masjid.distance_km < 1
              ? `${(masjid.distance_km * 1000).toFixed(0)} m away`
              : `${masjid.distance_km.toFixed(1)} km away`}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={() => { onToggleFavorite(masjid); }}
        disabled={!canAdd}
        aria-label={
          isFavorite
            ? `Remove ${masjid.name} from favorites`
            : `Save ${masjid.name} to favorites`
        }
        aria-pressed={isFavorite}
        className={[
          "ml-3 flex-shrink-0 rounded-full p-1.5 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
          isFavorite
            ? "text-emerald-600 hover:text-emerald-800"
            : canAdd
              ? "text-gray-300 hover:text-emerald-500"
              : "cursor-not-allowed text-gray-200",
        ].join(" ")}
        title={
          !canAdd ? "Favorites full (max 5) — remove one to add another" : ""
        }
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
      </button>
    </article>
  );
}
