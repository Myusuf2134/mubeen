import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { searchMasjids, type SearchParams } from "@/api/masjids";
import { MasjidCard } from "@/components/MasjidCard";
import { SearchBar } from "@/components/SearchBar";
import { useFavorites } from "@/hooks/useFavorites";
import { useAuth } from "@/context/AuthContext";
import type { MasjidSummary } from "@/types/api";

// Accurate Islamic 8-pointed star (outer r=45, inner r=20, center 50,50)
const STAR_POINTS =
  "50,5 57.65,31.52 81.82,18.18 68.48,42.35 95,50 68.48,57.65 81.82,81.82 " +
  "57.65,68.48 50,95 42.35,68.48 18.18,81.82 31.52,57.65 5,50 31.52,42.35 " +
  "18.18,18.18 42.35,31.52";

function IslamicStar({ className, fill = "currentColor" }: { className?: string; fill?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true" focusable="false">
      <polygon points={STAR_POINTS} fill={fill} />
    </svg>
  );
}

const FEATURES = [
  { icon: "🕌", title: "Masjid Directory", desc: "Search by name, city, or your location" },
  { icon: "📡", title: "Live Captions", desc: "Follow the khutbah in real time" },
  { icon: "🕐", title: "Prayer Times", desc: "Adhan & iqamah for every prayer" },
] as const;

export function HomePage() {
  const [results, setResults] = useState<MasjidSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const { favorites, addFavorite, removeFavorite, isFavorite, atCapacity } =
    useFavorites();

  const { isAuthenticated, clearToken } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    clearToken();
    navigate("/", { replace: true });
  }

  function handleSearch(params: SearchParams): void {
    setLoading(true);
    setError("");
    searchMasjids(params)
      .then((data) => {
        setResults(data);
        setSearched(true);
        setTimeout(() => { resultsRef.current?.focus(); }, 0);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Search failed.");
      })
      .finally(() => { setLoading(false); });
  }

  function handleToggleFavorite(masjid: MasjidSummary) {
    if (isFavorite(masjid.id)) removeFavorite(masjid.id);
    else addFavorite(masjid);
  }

  return (
    <div className="min-h-screen">

      {/* ── Admin nav ──────────────────────────────────────────────── */}
      <nav
        aria-label="Operator navigation"
        className="relative z-10 flex items-center justify-end gap-3 px-5 py-3"
      >
        {isAuthenticated ? (
          <>
            <Link
              to="/register-masjid"
              className="text-[11px] font-medium text-ink-muted transition-colors duration-150 hover:text-mint focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
            >
              My masjid
            </Link>
            <span className="h-3 w-px bg-white/15" aria-hidden="true" />
            <button
              type="button"
              onClick={handleSignOut}
              className="text-[11px] font-medium text-ink-muted transition-colors duration-150 hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link
              to="/signup"
              className="text-[11px] font-medium text-ink-muted transition-colors duration-150 hover:text-mint focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
            >
              Register your masjid
            </Link>
            <span className="h-3 w-px bg-white/15" aria-hidden="true" />
            <Link
              to="/login"
              className="text-[11px] font-medium text-ink-muted transition-colors duration-150 hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
            >
              For masjid admins
            </Link>
          </>
        )}
      </nav>

      {/* ── Ambient glow orbs (decorative, fixed) ──────────────────── */}
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className="absolute -top-1/4 -right-20 h-[700px] w-[700px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(94,234,212,0.09) 0%, transparent 65%)" }}
        />
        <div
          className="absolute bottom-0 -left-32 h-[600px] w-[600px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(212,176,106,0.06) 0%, transparent 65%)" }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[900px] w-[900px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(13,148,136,0.04) 0%, transparent 60%)" }}
        />
      </div>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden px-5 pb-10 pt-10 text-center">

        {/* Dot grid texture */}
        <div className="pointer-events-none absolute inset-0 dot-grid opacity-40" aria-hidden="true" />

        {/* Large centered background star */}
        <IslamicStar
          className="pointer-events-none absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 opacity-[0.028] star-float"
          fill="#5eead4"
        />

        {/* Corner accent stars */}
        <IslamicStar
          className="pointer-events-none absolute -top-8 -left-8 h-40 w-40 opacity-[0.10] rotate-12"
          fill="#5eead4"
        />
        <IslamicStar
          className="pointer-events-none absolute -bottom-6 -right-6 h-36 w-36 opacity-[0.07] rotate-45"
          fill="#d4b06a"
        />
        <IslamicStar
          className="pointer-events-none absolute top-4 right-12 h-16 w-16 opacity-[0.08] -rotate-12"
          fill="#5eead4"
        />

        {/* Eyebrow pill */}
        <motion.div
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="relative mb-7 flex justify-center"
        >
          <div
            className="inline-flex items-center gap-2 rounded-full border border-mint/25 bg-mint/[0.08] px-4 py-1.5 text-step--1 font-semibold text-mint"
            style={{ backdropFilter: "blur(12px)" }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full bg-mint animate-pulse"
              style={{ boxShadow: "0 0 8px #5eead4" }}
              aria-hidden="true"
            />
            Masjid directory · Prayer times · Live khutbah
          </div>
        </motion.div>

        {/* Brand lockup */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="relative"
        >
          {/* Icon + wordmark */}
          <div className="mb-6 flex items-center justify-center gap-4">
            <div
              className="flex h-[72px] w-[72px] items-center justify-center rounded-icon font-sora text-3xl font-black"
              style={{
                background: "linear-gradient(135deg, #5eead4 0%, #0d9488 100%)",
                color: "#06120f",
                boxShadow:
                  "0 0 50px rgba(94,234,212,0.28), 0 0 20px rgba(94,234,212,0.20), 0 4px 16px rgba(0,0,0,0.4)",
              }}
              aria-hidden="true"
            >
              M
            </div>
            <h1
              className="font-sora font-black tracking-sora heading-shimmer"
              style={{ fontSize: "clamp(3rem, 8vw, 4.5rem)", lineHeight: 1 }}
            >
              Mubeen
            </h1>
          </div>

          {/* Arabic subtitle */}
          <p
            className="mb-5 font-amiri select-none"
            style={{
              fontSize: "clamp(2rem, 5vw, 3rem)",
              lineHeight: 1.8,
              color: "rgba(212,176,106,0.65)",
              letterSpacing: "0.04em",
            }}
            lang="ar"
            dir="rtl"
            aria-label="Mubeen in Arabic"
          >
            مُبِين
          </p>

          {/* Tagline */}
          <p
            className="mx-auto max-w-sm text-ink-dim"
            style={{ fontSize: "var(--step-1)", lineHeight: 1.55 }}
          >
            Find your masjid, check prayer times,{" "}
            <br className="hidden sm:block" />
            and follow the khutbah live.
          </p>
        </motion.div>

        {/* Bottom gradient fade into content */}
        <div
          className="pointer-events-none absolute bottom-0 left-0 right-0 h-20"
          style={{ background: "linear-gradient(to bottom, transparent, var(--bg-0))" }}
          aria-hidden="true"
        />
      </section>

      {/* ── Search ─────────────────────────────────────────────────── */}
      <div className="mx-auto max-w-2xl px-5 pb-6">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.22, ease: "easeOut" }}
        >
          <SearchBar onSearch={handleSearch} loading={loading} />
        </motion.div>
      </div>

      {/* ── Feature strip (hidden once searched) ───────────────────── */}
      <AnimatePresence>
        {!searched && !loading && (
          <motion.div
            key="features"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8, transition: { duration: 0.2 } }}
            transition={{ duration: 0.4, delay: 0.32 }}
            className="mx-auto max-w-2xl px-5 pb-16"
          >
            <div className="grid grid-cols-3 gap-3">
              {FEATURES.map((feat, i) => (
                <motion.div
                  key={feat.title}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, delay: 0.36 + i * 0.07 }}
                  className="glass rounded-card p-4 text-center"
                  style={{ borderColor: "rgba(94,234,212,0.10)" }}
                >
                  <span className="mb-2 block text-2xl">{feat.icon}</span>
                  <p className="mb-1 font-sora font-semibold text-step--1 text-ink">
                    {feat.title}
                  </p>
                  <p className="text-[11px] text-ink-muted leading-snug">{feat.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Main content ───────────────────────────────────────────── */}
      <div className="mx-auto max-w-2xl px-5 pb-14">

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.p
              role="alert"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4 text-step--1 text-red-400"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        {/* Loading */}
        {loading && (
          <p role="status" className="mt-8 text-center text-step--1 text-ink-muted">
            Searching…
          </p>
        )}

        {/* Results */}
        {!loading && searched && (
          <section aria-label="Search results">
            <div
              ref={resultsRef}
              tabIndex={-1}
              className="mt-6 focus:outline-none"
              aria-live="polite"
              aria-atomic="true"
            >
              <h2 className="mb-4 kicker">
                {results.length === 0
                  ? "No masjids found"
                  : `${String(results.length)} masjid${results.length !== 1 ? "s" : ""} found`}
              </h2>
              <ul className="space-y-3">
                {results.map((m, i) => (
                  <motion.li
                    key={m.id}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.06, ease: "easeOut" }}
                  >
                    <MasjidCard
                      masjid={m}
                      isFavorite={isFavorite(m.id)}
                      onToggleFavorite={handleToggleFavorite}
                      atCapacity={atCapacity}
                    />
                  </motion.li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Saved favorites */}
        <AnimatePresence>
          {favorites.length > 0 && (
            <motion.section
              aria-label="Saved masjids"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35 }}
              className="mt-12"
            >
              <h2 className="kicker mb-4">Saved ({favorites.length}/5)</h2>
              <ul className="space-y-2">
                {favorites.map((m) => (
                  <li key={m.id}>
                    <motion.article
                      whileHover={{
                        y: -2,
                        borderColor: "rgba(94,234,212,0.20)",
                        transition: { type: "spring", stiffness: 400, damping: 30 },
                      }}
                      className="glass flex items-center gap-4 rounded-row px-4 py-3"
                    >
                      <div
                        className="h-9 w-9 flex-shrink-0 rounded-icon flex items-center justify-center text-base"
                        style={{
                          background:
                            "linear-gradient(135deg, rgba(94,234,212,0.15), rgba(212,176,106,0.12))",
                        }}
                        aria-hidden="true"
                      >
                        🕌
                      </div>
                      <div className="min-w-0 flex-1">
                        <Link
                          to={`/masjid/${m.id}`}
                          className="block truncate font-sora font-semibold text-step--1 text-ink transition-colors duration-150 hover:text-mint focus:outline-none focus-visible:ring-2 focus-visible:ring-mint focus-visible:rounded-sm"
                        >
                          {m.name}
                        </Link>
                        <p className="text-[11px] text-ink-muted">
                          {m.city}, {m.state}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => { removeFavorite(m.id); }}
                        aria-label={`Remove ${m.name} from saved`}
                        className="flex-shrink-0 text-ink-muted transition-colors duration-150 hover:text-red-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400 rounded-full p-1"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          className="h-4 w-4"
                          aria-hidden="true"
                        >
                          <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                        </svg>
                      </button>
                    </motion.article>
                  </li>
                ))}
              </ul>
            </motion.section>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}
