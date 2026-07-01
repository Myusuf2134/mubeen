import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { searchMasjids, type SearchParams } from "@/api/masjids";
import { MasjidCard } from "@/components/MasjidCard";
import { SearchBar } from "@/components/SearchBar";
import { useFavorites } from "@/hooks/useFavorites";
import type { MasjidSummary } from "@/types/api";

export function HomePage() {
  const [results, setResults] = useState<MasjidSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const { favorites, addFavorite, removeFavorite, isFavorite, atCapacity } =
    useFavorites();

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
      .finally(() => {
        setLoading(false);
      });
  }

  function handleToggleFavorite(masjid: MasjidSummary) {
    if (isFavorite(masjid.id)) {
      removeFavorite(masjid.id);
    } else {
      addFavorite(masjid);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Mubeen
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Find masjid prayer times near you
        </p>
      </header>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-600">
          {error}
        </p>
      )}

      {loading && (
        <p role="status" className="mt-6 text-center text-sm text-gray-500">
          Searching…
        </p>
      )}

      {/* Search results */}
      {!loading && searched && (
        <section aria-label="Search results">
          <div
            ref={resultsRef}
            tabIndex={-1}
            className="mt-6 focus:outline-none"
            aria-live="polite"
            aria-atomic="true"
          >
            <h2 className="mb-3 text-sm font-medium text-gray-600">
              {results.length === 0
                ? "No masjids found"
                : `${String(results.length)} masjid${results.length !== 1 ? "s" : ""} found`}
            </h2>
            <ul className="space-y-3">
              {results.map((m) => (
                <li key={m.id}>
                  <MasjidCard
                    masjid={m}
                    isFavorite={isFavorite(m.id)}
                    onToggleFavorite={handleToggleFavorite}
                    atCapacity={atCapacity}
                  />
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Saved favorites */}
      {favorites.length > 0 && (
        <section aria-label="Saved masjids" className="mt-10">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
            Saved ({favorites.length}/5)
          </h2>
          <ul className="space-y-3">
            {favorites.map((m) => (
              <li key={m.id}>
                <article className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm">
                  <div className="min-w-0 flex-1">
                    <Link
                      to={`/masjid/${m.id}`}
                      className="block truncate text-sm font-medium text-gray-900 hover:text-emerald-700 focus:outline-none focus-visible:underline"
                    >
                      {m.name}
                    </Link>
                    <p className="text-xs text-gray-500">
                      {m.city}, {m.state}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => { removeFavorite(m.id); }}
                    aria-label={`Remove ${m.name} from saved`}
                    className="ml-3 flex-shrink-0 text-gray-400 hover:text-red-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
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
                </article>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
