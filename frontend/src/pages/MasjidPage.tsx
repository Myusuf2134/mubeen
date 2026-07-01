import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getMasjid } from "@/api/masjids";
import { PrayerTimesTable } from "@/components/PrayerTimesTable";
import { useFavorites } from "@/hooks/useFavorites";
import type { MasjidDetail, MasjidSummary } from "@/types/api";

function toSummary(d: MasjidDetail): MasjidSummary {
  return {
    id: d.id,
    name: d.name,
    city: d.city,
    state: d.state,
    country: d.country,
    lat: d.lat,
    lon: d.lon,
  };
}

function formatTime(hhmmss: string): string {
  const [h, m] = hhmmss.split(":");
  const d = new Date();
  d.setHours(Number(h), Number(m), 0, 0);
  return d.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export function MasjidPage() {
  const { id } = useParams<{ id: string }>();
  const [masjid, setMasjid] = useState<MasjidDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { addFavorite, removeFavorite, isFavorite, atCapacity } =
    useFavorites();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getMasjid(id)
      .then(setMasjid)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load masjid.");
      })
      .finally(() => { setLoading(false); });
  }, [id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p role="status" className="text-sm text-gray-500">
          Loading…
        </p>
      </div>
    );
  }

  if (error || !masjid) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p role="alert" className="text-sm text-red-600">
          {error || "Masjid not found."}
        </p>
        <Link
          to="/"
          className="mt-4 inline-block text-sm text-emerald-600 hover:underline"
        >
          ← Back to search
        </Link>
      </div>
    );
  }

  const favorited = isFavorite(masjid.id);
  const summary = toSummary(masjid);

  function handleFavoriteToggle() {
    if (favorited) {
      removeFavorite(summary.id);
    } else {
      addFavorite(summary);
    }
  }

  const sortedJumuah = [...masjid.jumuah_times].sort(
    (a, b) => a.sort_order - b.sort_order,
  );

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      {/* Back link */}
      <nav aria-label="Breadcrumb">
        <Link
          to="/"
          className="text-sm text-emerald-600 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
        >
          ← Directory
        </Link>
      </nav>

      {/* Header */}
      <header className="mt-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            {masjid.name}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {masjid.address_line}, {masjid.city}, {masjid.state}{" "}
            {masjid.country !== "US" && masjid.country}
          </p>
          <div className="mt-2 flex flex-wrap gap-3 text-sm">
            {masjid.phone && (
              <a
                href={`tel:${masjid.phone}`}
                className="text-emerald-700 hover:underline"
              >
                {masjid.phone}
              </a>
            )}
            {masjid.website && (
              <a
                href={masjid.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-700 hover:underline"
              >
                Website ↗
              </a>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={handleFavoriteToggle}
          disabled={!favorited && atCapacity}
          aria-label={favorited ? "Remove from saved" : "Save masjid"}
          aria-pressed={favorited}
          title={
            !favorited && atCapacity
              ? "Favorites full (max 5)"
              : favorited
                ? "Remove from saved"
                : "Save masjid"
          }
          className={[
            "flex-shrink-0 rounded-full p-2 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
            favorited
              ? "text-emerald-600 hover:text-emerald-800"
              : !atCapacity
                ? "text-gray-300 hover:text-emerald-500"
                : "cursor-not-allowed text-gray-200",
          ].join(" ")}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill={favorited ? "currentColor" : "none"}
            stroke="currentColor"
            strokeWidth={favorited ? 0 : 1.5}
            className="h-6 w-6"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
            />
          </svg>
        </button>
      </header>

      {/* Live session banner */}
      {masjid.has_live_session && (
        <div className="mt-4 flex items-center gap-3 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
          </span>
          <span className="font-medium">Khutbah live now</span>
          <Link
            to={`/masjid/${masjid.id}/live`}
            className="ml-auto font-semibold underline underline-offset-2 hover:text-emerald-900"
          >
            Watch captions →
          </Link>
        </div>
      )}

      {/* Prayer times */}
      <section aria-labelledby="prayer-times-heading" className="mt-8">
        <h2
          id="prayer-times-heading"
          className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500"
        >
          Today's Prayer Times
        </h2>
        <PrayerTimesTable
          adhanTimes={masjid.adhan_times}
          iqamahTimes={masjid.iqamah_times}
        />
      </section>

      {/* Jumu'ah times */}
      {sortedJumuah.length > 0 && (
        <section aria-labelledby="jumuah-heading" className="mt-8">
          <h2
            id="jumuah-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500"
          >
            Jumu&apos;ah (Friday Prayer)
          </h2>
          <ul className="space-y-2">
            {sortedJumuah.map((jt) => (
              <li
                key={jt.id}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3"
              >
                <span
                  className="text-sm text-gray-800"
                  lang={jt.language}
                  dir={jt.language === "ar" ? "rtl" : undefined}
                >
                  {jt.label ?? "Jumuʿah"}
                </span>
                <span className="tabular-nums text-sm font-medium text-gray-900">
                  {formatTime(jt.time)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
