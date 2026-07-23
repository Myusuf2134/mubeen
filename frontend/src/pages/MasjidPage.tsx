import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion, type MotionProps } from "framer-motion";
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

function fadeRise(delay: number): Pick<MotionProps, "initial" | "animate" | "transition"> {
  return {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, delay, ease: "easeOut" },
  };
}

export function MasjidPage() {
  const { id } = useParams<{ id: string }>();
  const [masjid, setMasjid] = useState<MasjidDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { addFavorite, removeFavorite, isFavorite, atCapacity } = useFavorites();

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

  /* Loading state */
  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16 text-center">
        <p role="status" className="text-step--1 text-ink-muted">Loading…</p>
      </div>
    );
  }

  /* Error / not-found state */
  if (error || !masjid) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16 text-center">
        <p role="alert" className="text-step--1 text-red-400">
          {error || "Masjid not found."}
        </p>
        <Link
          to="/"
          className="mt-4 inline-block text-step--1 text-mint hover:underline"
        >
          ← Directory
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
    <div className="mx-auto max-w-2xl px-5 py-10">

      {/* ── Back nav ──────────────────────────────────────────────── */}
      <nav aria-label="Breadcrumb">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-step--1 text-ink-muted transition-colors duration-150 hover:text-mint focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"
               className="h-3.5 w-3.5" aria-hidden="true">
            <path fillRule="evenodd"
              d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
              clipRule="evenodd" />
          </svg>
          Directory
        </Link>
      </nav>

      {/* ── Header banner ─────────────────────────────────────────── */}
      <motion.div
        {...fadeRise(0.05)}
        className="relative mt-6 overflow-hidden rounded-card-xl glass"
        style={{
          borderColor: "rgba(94,234,212,0.12)",
          background:
            "linear-gradient(135deg, rgba(94,234,212,0.06) 0%, rgba(13,148,136,0.04) 50%, rgba(212,176,106,0.04) 100%)",
        }}
      >
        {/* Decorative Islamic star in banner corner */}
        <svg
          viewBox="0 0 100 100"
          className="pointer-events-none absolute -right-8 -top-8 h-40 w-40 opacity-[0.07] rotate-12"
          aria-hidden="true"
          focusable="false"
        >
          <polygon
            points={
              "50,5 57.65,31.52 81.82,18.18 68.48,42.35 95,50 68.48,57.65 " +
              "81.82,81.82 57.65,68.48 50,95 42.35,68.48 18.18,81.82 31.52,57.65 " +
              "5,50 31.52,42.35 18.18,18.18 42.35,31.52"
            }
            fill="#5eead4"
          />
        </svg>

        {/* Gradient top border line */}
        <div
          className="absolute top-0 left-0 right-0 h-px"
          style={{
            background:
              "linear-gradient(90deg, transparent 0%, rgba(94,234,212,0.5) 30%, rgba(212,176,106,0.4) 70%, transparent 100%)",
          }}
          aria-hidden="true"
        />

        <header className="relative flex items-start justify-between gap-4 px-6 py-6">
          <div className="min-w-0">
            {/* Avatar + name row */}
            <div className="mb-3 flex items-center gap-3">
              <div
                className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-icon text-xl"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(94,234,212,0.22), rgba(212,176,106,0.16))",
                  boxShadow: "0 2px 12px rgba(94,234,212,0.12)",
                }}
                aria-hidden="true"
              >
                🕌
              </div>
              <h1 className="font-sora text-step-3 font-bold tracking-sora text-ink">
                {masjid.name}
              </h1>
            </div>

            <p className="text-step--1 text-ink-muted">
              {masjid.address_line}, {masjid.city}, {masjid.state}
              {masjid.country !== "US" && ` ${masjid.country}`}
            </p>
            {(masjid.phone ?? masjid.website) && (
              <div className="mt-3 flex flex-wrap gap-3">
                {masjid.phone && (
                  <a
                    href={`tel:${masjid.phone}`}
                    className="text-step--1 text-mint hover:underline"
                  >
                    {masjid.phone}
                  </a>
                )}
                {masjid.website && (
                  <a
                    href={masjid.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-step--1 text-mint hover:underline"
                  >
                    Website ↗
                  </a>
                )}
              </div>
            )}
          </div>

          {/* Favourite toggle */}
          <motion.button
            type="button"
            whileTap={{ scale: 0.82 }}
            whileHover={{ scale: 1.12 }}
            onClick={handleFavoriteToggle}
            disabled={!favorited && atCapacity}
            aria-label={favorited ? "Remove from saved" : "Save masjid"}
            aria-pressed={favorited}
            title={!favorited && atCapacity ? "Favorites full (max 5)" : ""}
            className={[
              "flex-shrink-0 rounded-full p-2 transition-colors duration-150",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-mint",
              favorited
                ? "text-mint"
                : !atCapacity
                  ? "text-ink-muted hover:text-mint"
                  : "cursor-not-allowed opacity-30 text-ink-muted",
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
          </motion.button>
        </header>
      </motion.div>

      {/* ── Live session banner ────────────────────────────────────── */}
      {masjid.has_live_session && (
        <motion.div
          {...fadeRise(0.1)}
          className="glass mt-5 flex items-center gap-3 rounded-row px-4 py-3"
          style={{ borderColor: "rgba(248,113,113,0.25)" }}
        >
          {/* Pulsing dot */}
          <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-400" />
          </span>
          <span className="font-sora font-semibold text-step--1 text-red-300">
            Khutbah live now
          </span>
          <Link
            to={`/masjid/${masjid.id}/live`}
            className="ml-auto text-step--1 font-semibold text-red-300 underline underline-offset-2 hover:text-red-200"
          >
            Watch captions →
          </Link>
        </motion.div>
      )}

      {/* ── Prayer times ──────────────────────────────────────────── */}
      <motion.section
        {...fadeRise(0.15)}
        aria-labelledby="prayer-times-heading"
        className="mt-10"
      >
        <h2
          id="prayer-times-heading"
          className="kicker mb-4"
        >
          Today's Prayer Times
        </h2>
        <PrayerTimesTable
          adhanTimes={masjid.adhan_times}
          iqamahTimes={masjid.iqamah_times}
        />
      </motion.section>

      {/* ── Jumu'ah times ─────────────────────────────────────────── */}
      {sortedJumuah.length > 0 && (
        <motion.section
          {...fadeRise(0.22)}
          aria-labelledby="jumuah-heading"
          className="mt-10"
        >
          <h2 id="jumuah-heading" className="kicker mb-4">
            Jumu&apos;ah (Friday Prayer)
          </h2>
          <ul className="space-y-2">
            {sortedJumuah.map((jt) => (
              <motion.li
                key={jt.id}
                whileHover={{
                  y: -2,
                  borderColor: "rgba(94,234,212,0.20)",
                  transition: { type: "spring", stiffness: 400, damping: 30 },
                }}
                className="glass flex items-center justify-between rounded-row px-4 py-3.5"
              >
                <span
                  className="font-sora font-medium text-step--1 text-ink"
                  lang={jt.language}
                  dir={jt.language === "ar" ? "rtl" : undefined}
                >
                  {jt.language === "ar" ? (
                    <span className="font-amiri text-step-0">{jt.label ?? "Jumuʿah"}</span>
                  ) : (
                    jt.label ?? "Jumuʿah"
                  )}
                </span>
                <span className="tabular-nums text-step--1 font-semibold text-mint">
                  {formatTime(jt.time)}
                </span>
              </motion.li>
            ))}
          </ul>
        </motion.section>
      )}

    </div>
  );
}
