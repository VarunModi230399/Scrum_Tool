import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth-tokens";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function buildHeaders(init?: RequestInit): HeadersInit {
  const accessToken = getAccessToken();
  const isFormData = init?.body instanceof FormData;
  return {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...init?.headers,
  };
}

async function rawFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_BASE_URL}/api/v1${path}`, { ...init, headers: buildHeaders(init) });
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const res = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return false;

  const body = await res.json();
  setTokens(body.data.access_token, body.data.refresh_token);
  return true;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res = await rawFetch(path, init);

  if (res.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefresh();
    res = refreshed ? await rawFetch(path, init) : res;
    if (!refreshed) {
      clearTokens();
      if (typeof window !== "undefined") window.location.href = "/login";
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(
      res.status,
      body?.error?.code ?? "UNKNOWN_ERROR",
      body?.error?.message ?? res.statusText,
    );
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
