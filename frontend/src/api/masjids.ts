import type { MasjidDetail, MasjidSummary } from "@/types/api";

const BASE = "/api/masjids";

// ── Masjid registration ────────────────────────────────────────────────────────

export class MasjidApiError extends Error {
  constructor(
    message: string,
    public readonly field: string = "form",
    public readonly status: number = 400,
  ) {
    super(message);
    this.name = "MasjidApiError";
  }
}

export interface RegisterMasjidPayload {
  name: string;
  address_line: string;
  city: string;
  state: string;
  country: string;
  lat: number;
  lon: number;
  calculation_method: string;
  timezone: string;
  phone?: string;
  website?: string;
}

export interface RegisterMasjidResult {
  id: string;
  name: string;
  city: string;
  state: string;
  access_token: string;
}

function extractPydanticField(detail: unknown): string {
  if (!Array.isArray(detail) || detail.length === 0) return "form";
  const first = detail[0] as { loc?: unknown[] };
  const loc = first?.loc ?? [];
  return String(loc[loc.length - 1] ?? "form");
}

function extractPydanticMessage(detail: unknown): string {
  if (!Array.isArray(detail) || detail.length === 0) return "Validation error";
  const first = detail[0] as { msg?: string };
  return (first?.msg ?? "Validation error").replace(/^Value error,\s*/i, "");
}

export async function registerMasjidApi(
  payload: RegisterMasjidPayload,
  token: string,
): Promise<RegisterMasjidResult> {
  const resp = await fetch(BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (resp.status === 201) {
    return resp.json() as Promise<RegisterMasjidResult>;
  }

  const body = (await resp.json().catch(() => ({}))) as Record<string, unknown>;

  if (resp.status === 409) {
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : "A masjid with these details already exists.";
    throw new MasjidApiError(detail, "form", 409);
  }

  if (resp.status === 422) {
    const field = extractPydanticField(body.detail);
    const message = extractPydanticMessage(body.detail);
    const mappedField = field === "name" || field === "timezone" ? field : "form";
    throw new MasjidApiError(message, mappedField, 422);
  }

  if (resp.status === 401) {
    throw new MasjidApiError("Session expired. Please sign in again.", "form", 401);
  }

  throw new MasjidApiError(
    `Registration failed (${String(resp.status)}). Please try again.`,
    "form",
    resp.status,
  );
}

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
