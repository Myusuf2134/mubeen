// Session management API — start/stop khutbah sessions.

export interface StartSessionResponse {
  session_id: string;
  masjid_id: string;
  started_at: string;
}

export interface StopSessionResponse {
  session_id: string;
  ended_at: string;
}

export async function startSession(
  masjidId: string,
  token: string,
): Promise<StartSessionResponse> {
  const resp = await fetch(`/api/khutbah/${masjidId}/start`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : 'Failed to start session';
    throw new Error(detail);
  }

  return resp.json() as Promise<StartSessionResponse>;
}

export async function stopSession(
  masjidId: string,
  token: string,
): Promise<StopSessionResponse> {
  const resp = await fetch(`/api/khutbah/${masjidId}/stop`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : 'Failed to stop session';
    throw new Error(detail);
  }

  return resp.json() as Promise<StopSessionResponse>;
}
