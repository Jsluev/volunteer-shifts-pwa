const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StoredUser {
  id: number;
  email: string;
  role: string;
  full_name: string;
  tenant_id: number;
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function storeAuth(accessToken: string, refreshToken: string, user: StoredUser) {
  localStorage.setItem("token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
  localStorage.setItem("user", JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

async function tryRefresh(): Promise<string> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) throw new Error("No refresh token");

  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = fetch(`${API}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  }).then(async (res) => {
    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data.access_token as string;
  }).finally(() => {
    isRefreshing = false;
    refreshPromise = null;
  });

  return refreshPromise;
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res = await fetch(`${API}${path}`, { ...options, headers });

  if (res.status === 401 && typeof window !== "undefined") {
    try {
      const newToken = await tryRefresh();
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${API}${path}`, { ...options, headers });
    } catch {
      clearAuth();
      window.location.href = "/";
      throw new Error("Unauthorized");
    }
  }

  if (res.status === 401) {
    clearAuth();
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Request failed");
  }

  return res.json();
}
