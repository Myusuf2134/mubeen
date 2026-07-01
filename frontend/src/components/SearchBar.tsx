import { useRef, useState } from "react";
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
  const [geoStatus, setGeoStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(
    null,
  );
  const [geoError, setGeoError] = useState("");
  const firstInputRef = useRef<HTMLInputElement>(null);

  function handleModeChange(next: SearchMode) {
    setMode(next);
    // Reset geo state when switching away
    if (next !== "near-me") {
      setCoords(null);
      setGeoStatus("idle");
    }
    setTimeout(() => firstInputRef.current?.focus(), 0);
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

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      {/* Mode tabs */}
      <div
        role="tablist"
        aria-label="Search method"
        className="mb-4 flex gap-1 rounded-lg bg-gray-100 p-1"
      >
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            role="tab"
            aria-selected={mode === id}
            type="button"
            onClick={() => { handleModeChange(id); }}
            className={[
              "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
              mode === id
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700",
            ].join(" ")}
          >
            {label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {mode === "name" && (
          <div className="flex gap-2">
            <label htmlFor="search-name" className="sr-only">
              Masjid name
            </label>
            <input
              id="search-name"
              ref={firstInputRef}
              type="search"
              value={nameQuery}
              onChange={(e) => { setNameQuery(e.target.value); }}
              placeholder="Search by name…"
              autoComplete="off"
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="submit"
              disabled={!nameQuery.trim() || loading}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-40 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
            >
              Search
            </button>
          </div>
        )}

        {mode === "city" && (
          <div className="flex gap-2">
            <label htmlFor="search-city" className="sr-only">
              City
            </label>
            <input
              id="search-city"
              ref={firstInputRef}
              type="search"
              value={cityQuery}
              onChange={(e) => { setCityQuery(e.target.value); }}
              placeholder="Enter city name…"
              autoComplete="off"
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="submit"
              disabled={!cityQuery.trim() || loading}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-40 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
            >
              Search
            </button>
          </div>
        )}

        {mode === "near-me" && (
          <div>
            {geoStatus === "idle" && (
              <button
                type="button"
                onClick={requestLocation}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-emerald-600 px-4 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
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
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
                  />
                </svg>
                Use my location
              </button>
            )}
            {geoStatus === "loading" && (
              <p
                role="status"
                className="py-2 text-center text-sm text-gray-500"
              >
                Getting your location…
              </p>
            )}
            {geoStatus === "ready" && coords && (
              <div className="flex gap-2">
                <p className="flex-1 self-center text-sm text-gray-600">
                  Location found — searching nearby masjids
                </p>
                <button
                  type="button"
                  onClick={requestLocation}
                  className="text-xs text-emerald-600 hover:underline"
                >
                  Refresh
                </button>
              </div>
            )}
            {geoStatus === "error" && (
              <p role="alert" className="text-sm text-red-600">
                {geoError}
              </p>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
