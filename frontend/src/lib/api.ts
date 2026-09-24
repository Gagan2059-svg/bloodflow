/**
 * BloodFlow API client — all calls to FastAPI backend.
 * Reads NEXT_PUBLIC_API_URL from env (defaults to localhost:8000).
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("bloodflow_token");
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    // Token expired — clear and redirect
    if (typeof window !== "undefined") {
      localStorage.removeItem("bloodflow_token");
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail || `API Error ${res.status}`);
  }
  // 204 No Content
  if (res.status === 204) return {} as T;
  return res.json();
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    body,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  localStorage.setItem("bloodflow_token", data.access_token);
  return data;
}

export async function getMe() {
  return apiFetch<any>("/auth/me");
}

// ─── Facilities ───────────────────────────────────────────────────────────────
export async function getFacilities(skip = 0, limit = 100) {
  return apiFetch<any[]>(`/facilities/?skip=${skip}&limit=${limit}`);
}

// ─── Inventory ────────────────────────────────────────────────────────────────
export async function getInventory(params: Record<string, string | number> = {}) {
  const q = new URLSearchParams(params as any).toString();
  return apiFetch<any>(`/inventory/?${q}`);
}

export async function getInventorySummary(facilityId?: string) {
  const q = facilityId ? `?facility_id=${facilityId}` : "";
  return apiFetch<any>(`/inventory/summary${q}`);
}

// ─── Alerts ───────────────────────────────────────────────────────────────────
export async function getAlerts(params: Record<string, string> = {}) {
  const q = new URLSearchParams(params).toString();
  return apiFetch<any[]>(`/alerts/?${q}`);
}

export async function acknowledgeAlert(id: string) {
  return apiFetch<any>(`/alerts/${id}/acknowledge`, { method: "POST" });
}

export async function resolveAlert(id: string) {
  return apiFetch<any>(`/alerts/${id}/resolve`, { method: "POST" });
}

// ─── Recommendations ──────────────────────────────────────────────────────────
export async function getRecommendations(params: Record<string, string> = {}) {
  const q = new URLSearchParams(params).toString();
  return apiFetch<any[]>(`/recommendations/?${q}`);
}

export async function approveRecommendation(id: string) {
  return apiFetch<any>(`/recommendations/${id}/approve`, { method: "POST" });
}

export async function rejectRecommendation(id: string) {
  return apiFetch<any>(`/recommendations/${id}/reject`, { method: "POST" });
}

export async function runOptimizer() {
  return apiFetch<any>("/recommendations/run-optimizer", { method: "POST" });
}

// ─── Transfers ────────────────────────────────────────────────────────────────
export async function getTransfers(params: Record<string, string> = {}) {
  const q = new URLSearchParams(params).toString();
  return apiFetch<any[]>(`/transfers/?${q}`);
}

export async function createTransfer(payload: any) {
  return apiFetch<any>("/transfers/", { method: "POST", body: JSON.stringify(payload) });
}

// ─── Risk ─────────────────────────────────────────────────────────────────────
export async function getNetworkRisk() {
  return apiFetch<any>("/risk/network-summary");
}

export async function getFacilityRisk(facilityId: string) {
  return apiFetch<any>(`/risk/facility/${facilityId}`);
}

// ─── Forecasting ──────────────────────────────────────────────────────────────
export async function generateForecast(facilityId: string, bloodGroup: string, component: string, horizonDays = 7) {
  return apiFetch<any>(`/forecasting/generate?facility_id=${facilityId}&blood_group=${encodeURIComponent(bloodGroup)}&component=${component}&horizon_days=${horizonDays}`, {
    method: "POST",
  });
}

// ─── Anomalies ────────────────────────────────────────────────────────────────
export async function detectAnomaly(payload: any) {
  return apiFetch<any>("/anomalies/detect", { method: "POST", body: JSON.stringify(payload) });
}

// ─── Simulation (Digital Twin) ────────────────────────────────────────────────
export async function runSimulation(facilities: any[], scenario: any) {
  return apiFetch<any>("/simulations/run", {
    method: "POST",
    body: JSON.stringify({ facilities, scenario }),
  });
}

// ─── Explainability ───────────────────────────────────────────────────────────
export async function explainDecision(query: string, facilityId?: string) {
  return apiFetch<any>("/explain/", {
    method: "POST",
    body: JSON.stringify({ query, facility_id: facilityId }),
  });
}
