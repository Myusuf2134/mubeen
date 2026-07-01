import type { MasjidDetail, MasjidSummary } from "@/types/api";

const BASE = "/api/masjids";

export interface SearchParams {
  q?: string;
  city?: string;
  lat?: number;
  lon?: number;
  limit?: number;
}

export async function searchMasjids(
  params: SearchParams,
): Promise<MasjidSummary[]> {
  const url = new URL(BASE + "/search", window.location.origin);
  if (params.q) url.searchParams.set("q", params.q);
  if (params.city) url.searchParams.set("city", params.city);
  if (params.lat != null) url.searchParams.set("lat", String(params.lat));
  if (params.lon != null) url.searchParams.set("lon", String(params.lon));
  if (params.limit != null) url.searchParams.set("limit", String(params.limit));

  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(`Search failed: ${String(resp.status)}`);
  return resp.json() as Promise<MasjidSummary[]>;
}

export async function getMasjid(id: string): Promise<MasjidDetail> {
  const resp = await fetch(`${BASE}/${id}`);
  if (resp.status === 404) throw new Error("Masjid not found");
  if (!resp.ok) throw new Error(`Failed to load masjid: ${String(resp.status)}`);
  return resp.json() as Promise<MasjidDetail>;
}
