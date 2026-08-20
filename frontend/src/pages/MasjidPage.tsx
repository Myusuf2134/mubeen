import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion, type MotionProps } from "framer-motion";
import { getMasjid } from "@/api/masjids";
import { PrayerTimesTable } from "@/components/PrayerTimesTable";
import { MubeenLogo } from "@/components/MubeenLogo";
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
  const [activeTab, setActiveTab] = useState("About");

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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p role="status" className="text-step--1 text-ink-muted">Loading…</p>
      </div>
    );
  }

  if (error || !masjid) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p role="alert" className="text-step--1 text-red-400">
          {error || "Masjid not found."}
        </p>
        <Link to="/" className="text-step--1 text-mint hover:underline">
          ← Directory
        </Link>
      </div>
    );
  }

  const favorited = isFavorite(masjid.id);
  const summary = toSummary(masjid);
  const sortedJumuah = [...masjid.jumuah_times].sort((a, b) => a.sort_order - b.sort_order);

  function handleFavoriteToggle() {
    if (favorited) {
      removeFavorite(summary.id);
    } else {
      addFavorite(summary);
    }
  }

  // Navigate to Google Maps
  function handleGetDirections() {
    window.open(
      `https://www.google.com/maps/search/${encodeURIComponent(`${masjid.address_line}, ${masjid.city}, ${masjid.state}`)}`,
      "_blank",
      "noopener,noreferrer"
    );
  }

  const tabs = [
    { label: "About", id: "About" },
    { label: "Imams", id: "Imams" },
    { label: "Events", id: "Events" },
    { label: "Announcements", id: "Announcements" },
    { label: "Khutbahs", id: "Khutbahs" },
    { label: "Location", id: "Location" },
  ];

  return (
    <div className="flex flex-col min-h-screen" style={{ backgroundColor: "#ffffff" }}>
      {/* ─────── HEADER ───────── */}
      <header
        className="sticky top-0 z-40 flex items-center justify-between gap-6 px-6 py-4 border-b"
        style={{ backgroundColor: "#f9fafb", borderColor: "#e5e7eb" }}
      >
        {/* Left: Logo + Nav */}
        <div className="flex items-center gap-8">
          <Link to="/" className="flex-shrink-0 hover:opacity-80 transition-opacity">
            <MubeenLogo size={40} />
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link
              to="/"
              className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
            >
              Home
            </Link>
            <Link
              to="/"
              className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
            >
              Masjids
            </Link>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); }}
              className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
              title="Coming soon"
            >
              Live Khutbah
            </a>
            <div className="relative group">
              <button
                className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
                title="Coming soon"
              >
                Events
              </button>
            </div>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); }}
              className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
              title="Coming soon"
            >
              About
            </a>
          </nav>
        </div>

        {/* Right: Operator Login */}
        <Link
          to="/login"
          className="px-6 py-2 rounded-lg font-semibold text-white transition-colors"
          style={{ backgroundColor: "#2d8659" }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#1f5c3f")}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#2d8659")}
        >
          Operator Login
        </Link>
      </header>

      {/* ─────── HERO SECTION ───────── */}
      <section className="flex-1 flex">
        {/* Left: Image placeholder with gradient + pattern */}
        <motion.div
          {...fadeRise(0.1)}
          className="w-5/12 relative overflow-hidden"
          style={{
            background: "linear-gradient(180deg, #e8dcc8 0%, #c9a574 100%)",
          }}
        >
          {/* Islamic star pattern overlay — reuse from tv-display and login */}
          <svg
            aria-hidden="true"
            className="absolute inset-0 w-full h-full"
            viewBox="0 0 200 200"
            preserveAspectRatio="xMidYMid slice"
            style={{ opacity: 0.12 }}
          >
            <defs>
              <pattern id="masjid-detail-islamic-stars" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M25 5 L30 20 L45 25 L30 30 L25 45 L20 30 L5 25 L20 20 Z" fill="#1a1a1a" />
                <path d="M25 25 L35 25 L25 35 L15 25 Z" fill="#1a1a1a" />
              </pattern>
            </defs>
            <rect width="200" height="200" fill="url(#masjid-detail-islamic-stars)" />
          </svg>

          {/* TODO: Replace gradient + pattern with real masjid photo
              When available, update to:
              <img src={masjidPhotoUrl} alt={masjid.name} className="w-full h-full object-cover" />
              or set background-image on this div via inline style
          */}
        </motion.div>

        {/* Right: Masjid info card */}
        <motion.div
          {...fadeRise(0.15)}
          className="w-7/12 flex flex-col justify-start p-12 gap-6"
          style={{ backgroundColor: "#ffffff" }}
        >
          {/* Masjid name (serif) */}
          <div>
            <h1
              className="font-amiri font-bold text-ink mb-2"
              style={{ fontSize: "var(--step-4)", color: "#1a1a1a" }}
            >
              {masjid.name}
            </h1>

            {/* Verified badge — would show here if moderation_status data exists in backend
                Currently hidden since field not available in MasjidDetail type
                TODO: Uncomment when moderation_status is added to API
                {masjid.moderation_status === 'approved' && (
                  <div className="flex items-center gap-2 mb-4 text-green-700">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Verified Masjid
                  </div>
                )}
            */}
          </div>

          {/* Location with pin icon */}
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" style={{ color: "#666666" }}>
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-medium text-gray-900">
                {masjid.city}, {masjid.state}
                {masjid.country !== "US" && ` ${masjid.country}`}
              </p>
              <p className="text-sm text-gray-600 mt-1">{masjid.address_line}</p>
            </div>
          </div>

          {/* Description */}
          <p className="text-gray-700 leading-relaxed" style={{ fontSize: "var(--step-0)" }}>
            A place of worship, learning, and community for everyone.
          </p>

          {/* Buttons: Watch Live + Get Directions */}
          <div className="flex gap-4 mt-2">
            {masjid.has_live_session && (
              <Link
                to={`/display/${masjid.id}`} target="_blank" rel="noopener noreferrer"
                className="px-6 py-3 rounded-lg font-semibold text-white flex items-center gap-2 transition-colors"
                style={{ backgroundColor: "#2d8659" }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#1f5c3f")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#2d8659")}
              >
                <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-400" />
                </span>
                Watch Live Khutbah
              </Link>
            )}
            <button
              onClick={handleGetDirections}
              className="px-6 py-3 rounded-lg font-semibold border-2 text-gray-900 transition-colors"
              style={{ borderColor: "#d1d5db" }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f3f4f6")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
            >
              Get Directions
            </button>
          </div>
        </motion.div>
      </section>

      {/* ─────── PRAYER TIMES + LIVE SECTION ───────── */}
      <section className="flex gap-6 px-6 py-10 max-w-6xl mx-auto w-full">
        {/* Prayer times card (left) */}
        <motion.div
          {...fadeRise(0.2)}
          className="flex-1 rounded-lg p-6"
          style={{ backgroundColor: "#f9fafb", border: "1px solid #e5e7eb" }}
        >
          <h2 className="font-bold text-lg mb-6" style={{ color: "#1a1a1a" }}>
            TODAY'S PRAYER TIMES
          </h2>
          <PrayerTimesTable
            adhanTimes={masjid.adhan_times}
            iqamahTimes={masjid.iqamah_times}
          />
        </motion.div>

        {/* Live session / Info card (right) */}
        <motion.div
          {...fadeRise(0.25)}
          className="flex-1 rounded-lg p-6"
          style={{ backgroundColor: "#f9fafb", border: "1px solid #e5e7eb" }}
        >
          {masjid.has_live_session ? (
            <div>
              {/* LIVE NOW indicator */}
              <div className="flex items-center gap-2 mb-4">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
                </span>
                <span className="font-bold text-red-600 text-sm">LIVE NOW</span>
              </div>

              {/* Khutbah title */}
              <h3 className="font-bold text-lg mb-2" style={{ color: "#1a1a1a" }}>
                Friday Khutbah
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Arabic & English captions available
              </p>

              {/* Watch Live button */}
              <Link
                to={`/display/${masjid.id}`} target="_blank" rel="noopener noreferrer"
                className="w-full px-4 py-3 rounded-lg font-semibold text-white text-center transition-colors block"
                style={{ backgroundColor: "#2d8659" }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#1f5c3f")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#2d8659")}
              >
                Watch Live
              </Link>
            </div>
          ) : (
            <div>
              <h3 className="font-bold text-lg mb-2" style={{ color: "#1a1a1a" }}>
                No Live Session
              </h3>
              <p className="text-sm text-gray-600">
                A khutbah will appear here when live.
              </p>
            </div>
          )}

          {/* Address card below live section */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" style={{ color: "#2d8659" }}>
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="font-medium text-sm text-gray-900">
                  {masjid.address_line}
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  {masjid.city}, {masjid.state}
                </p>
                <button
                  onClick={handleGetDirections}
                  className="text-xs font-medium mt-2 transition-colors"
                  style={{ color: "#2d8659" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#1f5c3f")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "#2d8659")}
                >
                  View on Maps →
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ─────── TABS SECTION ───────── */}
      <section className="px-6 py-8 max-w-6xl mx-auto w-full border-t border-gray-200">
        {/* Tab buttons */}
        <div className="flex gap-8 border-b border-gray-200 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 font-medium text-sm transition-colors border-b-2 ${
                activeTab === tab.id
                  ? "text-gray-900 border-b-gray-900"
                  : "text-gray-600 border-b-transparent hover:text-gray-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="prose prose-sm max-w-none">
          {activeTab === "About" && (
            <div>
              <p className="text-gray-700 leading-relaxed">
                {masjid.name} is dedicated to serving the community through prayer, education, and outreach. All are welcome.
              </p>
            </div>
          )}

          {activeTab === "Imams" && (
            <div className="text-gray-600">
              <p>Coming soon</p>
            </div>
          )}

          {activeTab === "Events" && (
            <div className="text-gray-600">
              <p>Coming soon</p>
            </div>
          )}

          {activeTab === "Announcements" && (
            <div className="text-gray-600">
              <p>Coming soon</p>
            </div>
          )}

          {activeTab === "Khutbahs" && (
            <div className="text-gray-600">
              <p>Coming soon</p>
            </div>
          )}

          {activeTab === "Location" && (
            <div>
              <p className="text-gray-700 mb-4">
                {masjid.address_line}<br />
                {masjid.city}, {masjid.state} {masjid.country}
              </p>
              {masjid.phone && (
                <p>
                  <strong>Phone:</strong>{" "}
                  <a href={`tel:${masjid.phone}`} className="text-blue-600 hover:underline">
                    {masjid.phone}
                  </a>
                </p>
              )}
              {masjid.website && (
                <p>
                  <strong>Website:</strong>{" "}
                  <a
                    href={masjid.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {masjid.website}
                  </a>
                </p>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Spacer */}
      <div className="flex-1" />
    </div>
  );
}
