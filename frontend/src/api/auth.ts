export class AuthApiError extends Error {
  constructor(
    message: string,
    public readonly field: "email" | "password" | "form" = "form",
  ) {
    super(message);
    this.name = "AuthApiError";
  }
}

export interface LoginResult {
  access_token: string;
  token_type: string;
}

function extractPydanticMessage(detail: unknown): string {
  if (!Array.isArray(detail) || detail.length === 0) return "Validation error";
  const first = detail[0] as { msg?: string; loc?: string[] };
  return (first?.msg ?? "Validation error").replace(/^Value error,\s*/i, "");
}

export async function signupApi(email: string, password: string): Promise<void> {
  const resp = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (resp.status === 201) return;

  const body = (await resp.json().catch(() => ({}))) as Record<string, unknown>;

  if (resp.status === 409) {
    throw new AuthApiError(
      typeof body.detail === "string" ? body.detail : "Email already registered",
      "email",
    );
  }
  if (resp.status === 422) {
    const detail = body.detail;
    const message = extractPydanticMessage(detail);
    const firstLoc =
      (Array.isArray(detail) && (detail[0] as { loc?: string[] })?.loc) || [];
    const lastField = firstLoc[firstLoc.length - 1];
    throw new AuthApiError(message, lastField === "password" ? "password" : "form");
  }
  throw new AuthApiError(`Signup failed (${String(resp.status)})`);
}

export async function loginApi(email: string, password: string): Promise<LoginResult> {
  const resp = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (resp.ok) return resp.json() as Promise<LoginResult>;

  const body = (await resp.json().catch(() => ({}))) as Record<string, unknown>;

  if (resp.status === 401) {
    throw new AuthApiError(
      typeof body.detail === "string" ? body.detail : "Invalid email or password",
      "form",
    );
  }
  throw new AuthApiError(`Login failed (${String(resp.status)})`);
}
