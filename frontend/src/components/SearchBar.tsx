import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { SearchParams } from "@/api/masjids";

type SearchMode = "name" | "city" | "near-me";

interface Props {
  onSearch: (params: SearchParams) => void;
  loading: boolean;
}

export function SearchBar({ onSearch, loading }: Props) {
  const [mode, setMode] = useState<SearchMode>("name");
  const [nameQuery, setNameQuery] = useState("");
  const [cityQuery, setCityQuery] = useState("");
  const [geoStatus, setGeoStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [geoError, setGeoError] = useState("");
  const firstInputRef = useRef<HTMLInputElement>(null);

  function handleModeChange(next: SearchMode) {
    setMode(next);
    if (next !== "near-me") {
      setCoords(null);
      setGeoStatus("idle");
    }
    setTimeout(() => { firstInputRef.current?.focus(); }, 0);
  }

  function requestLocation() {
    if (!("geolocation" in navigator)) {
      setGeoError("Geolocation not supported by this browser.");
      setGeoStatus("error");
      return;
    }
    setGeoStatus("loading");
    navigator.geolocation.getCurrentPosition(
      ({ coords: c }) => {
        setCoords({ lat: c.latitude, lon: c.longitude });
        setGeoStatus("ready");
        onSearch({ lat: c.latitude, lon: c.longitude });
      },
      (err) => {
        setGeoError(err.message);
        setGeoStatus("error");
      },
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "name" && nameQuery.trim()) {
      onSearch({ q: nameQuery.trim() });
    } else if (mode === "city" && cityQuery.trim()) {
      onSearch({ city: cityQuery.trim() });
    } else if (mode === "near-me" && coords) {
      onSearch(coords);
    }
  }

  const tabs: { id: SearchMode; label: string }[] = [
    { id: "name", label: "By name" },
    { id: "city", label: "By city" },
    { id: "near-me", label: "Near me" },
  ];

  /* Shared dark input style */
  const inputCls =
    "flex-1 rounded-full bg-white/5 border border-white/10 px-4 py-2.5 text-step--1 " +
    "text-ink placeholder-ink-muted focus:outline-none focus:border-mint/50 " +
    "focus:ring-1 focus:ring-mint/30 transition-colors duration-150";

  return (
    <div className="glass rounded-card-lg p-5">
      {/* Tab strip */}
      <div
        role="tablist"
        aria-label="Search method"
        className="relative mb-4 flex rounded-full bg-white/5 p-1"
      >
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            role="tab"
            aria-selected={mode === id}
            type="button"
            onClick={() => { handleModeChange(id); }}
            className="relative flex-1 rounded-full px-3 py-1.5 text-step--1 font-medium transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-mint"
            style={{ zIndex: 1 }}
          >
            {/* Animated pill indicator sits behind text */}
            {mode === id && (
              <motion.span
                layoutId="tab-indicator"
                className="absolute inset-0 rounded-full"
                style={{
                  background: "linear-gradient(135deg, #5eead4 0%, #0d9488 100%)",
                  zIndex: -1,
                }}
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              />
            )}
            <span className={mode === id ? "text-[#062017] font-semibold" : "text-ink-muted"}>
              {label}
            </span>
          </button>
        ))}
      </div>

      {/* Form body */}
      <form onSubmit={handleSubmit}>
        <AnimatePresence mode="wait">
          {mode === "name" && (
            <motion.div
              key="name"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
              className="flex gap-2"
            >
              <label htmlFor="search-name" className="sr-only">Masjid name</label>
              <input
                id="search-name"
                ref={firstInputRef}
                type="search"
                value={nameQuery}
                onChange={(e) => { setNameQuery(e.target.value); }}
                placeholder="Search by name…"
                autoComplete="off"
                className={inputCls}
              />
              <button
                type="submit"
                disabled={!nameQuery.trim() || loading}
                className="btn-primary px-5 py-2.5 disabled:opacity-40"
              >
                {loading ? "…" : "Search"}
              </button>
            </motion.div>
          )}

          {mode === "city" && (
            <motion.div
              key="city"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
              className="flex gap-2"
            >
              <label htmlFor="search-city" className="sr-only">City</label>
              <input
                id="search-city"
                ref={firstInputRef}
                type="search"
                value={cityQuery}
                onChange={(e) => { setCityQuery(e.target.value); }}
                placeholder="Enter city name…"
                autoComplete="off"
                className={inputCls}
              />
              <button
                type="submit"
                disabled={!cityQuery.trim() || loading}
                className="btn-primary px-5 py-2.5 disabled:opacity-40"
              >
                {loading ? "…" : "Search"}
              </button>
            </motion.div>
          )}

          {mode === "near-me" && (
            <motion.div
              key="near-me"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              {geoStatus === "idle" && (
                <button
                  type="button"
                  onClick={requestLocation}
                  className="btn-ghost w-full justify-center py-2.5"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={1.5}
                    className="h-4 w-4"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round"
                      d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round"
                      d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                  </svg>
                  Use my location
                </button>
              )}
              {geoStatus === "loading" && (
                <p role="status" className="py-2.5 text-center text-step--1 text-ink-muted">
                  Getting your location…
                </p>
              )}
              {geoStatus === "ready" && coords && (
                <div className="flex items-center gap-3">
                  <p className="flex-1 text-step--1 text-ink-dim">
                    Location found — searching nearby masjids
                  </p>
                  <button
                    type="button"
                    onClick={requestLocation}
                    className="text-step--1 text-mint hover:underline"
                  >
                    Refresh
                  </button>
                </div>
              )}
              {geoStatus === "error" && (
                <p role="alert" className="text-step--1 text-red-400">
                  {geoError}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </form>
    </div>
  );
}
