const API_BASE = import.meta.env.VITE_API_URL || "/api";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  tenant_name: string;
}

export interface DashboardStats {
  total: number;
  pending: number;
  flagged: number;
  approved: number;
  locked: number;
  by_source: Record<string, number>;
  by_scope: Record<string, number>;
}

export interface Activity {
  id: string;
  source_type: string;
  source_type_display: string;
  source_reference: string;
  scope: string;
  scope_display: string;
  category: string;
  category_display: string;
  activity_date: string;
  period_start: string | null;
  period_end: string | null;
  description: string;
  site_code: string;
  site_name: string;
  quantity: string;
  unit: string;
  original_quantity: string | null;
  original_unit: string;
  status: string;
  status_display: string;
  flag_reason: string;
  analyst_notes: string;
  is_edited: boolean;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface IngestionRun {
  id: string;
  source_type: string;
  source_type_display: string;
  filename: string;
  status: string;
  status_display: string;
  rows_success: number;
  rows_failed: number;
  rows_flagged: number;
  rows_duplicate: number;
  error_summary: string;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access: string; refresh: string }>("/auth/token/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  me: () => request<User>("/me/"),

  dashboard: () => request<DashboardStats>("/review/dashboard/"),

  activities: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<Paginated<Activity>>(`/activities/${qs}`);
  },

  ingestionRuns: () => request<Paginated<IngestionRun>>("/ingestion/runs/"),

  upload: (sourceType: string, file: File) => {
    const form = new FormData();
    form.append("source_type", sourceType);
    form.append("file", file);
    return request<IngestionRun>("/ingestion/upload/", { method: "POST", body: form });
  },

  bulkReview: (activityIds: string[], action: string, flagReason?: string) =>
    request<Activity[]>("/review/bulk/", {
      method: "POST",
      body: JSON.stringify({ activity_ids: activityIds, action, flag_reason: flagReason || "" }),
    }),

  editActivity: (id: string, data: Partial<Activity>) =>
    request<Activity>(`/review/activities/${id}/edit/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
