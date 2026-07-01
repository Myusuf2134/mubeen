import { useCallback, useEffect, useState } from "react";
import type { MasjidSummary } from "@/types/api";

const STORAGE_KEY = "mubeen:favorites";
const MAX_FAVORITES = 5;

function loadFromStorage(): MasjidSummary[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as MasjidSummary[]) : [];
  } catch {
    return [];
  }
}

export function useFavorites() {
  const [favorites, setFavorites] = useState<MasjidSummary[]>(loadFromStorage);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
  }, [favorites]);

  const addFavorite = useCallback((masjid: MasjidSummary) => {
    setFavorites((prev) => {
      if (prev.some((m) => m.id === masjid.id)) return prev;
      return [masjid, ...prev].slice(0, MAX_FAVORITES);
    });
  }, []);

  const removeFavorite = useCallback((id: string) => {
    setFavorites((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const isFavorite = useCallback(
    (id: string) => favorites.some((m) => m.id === id),
    [favorites],
  );

  return {
    favorites,
    addFavorite,
    removeFavorite,
    isFavorite,
    atCapacity: favorites.length >= MAX_FAVORITES,
  };
}
