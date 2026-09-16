/**
 * LeadScout API Configuration & Central Client
 *
 * Set NEXT_PUBLIC_API_URL in your .env.local to point to the backend.
 * All API calls use this base URL.
 *
 * Example:
 *   NEXT_PUBLIC_API_URL=http://localhost:8000
 *
 * Auth strategy: JWT stored in localStorage, sent via Authorization: Bearer header.
 * The backend also sets an HttpOnly cookie (leadscout_access_token) for cookie-based auth.
 */

export const API_BASE_URL = (() => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  const isBrowser = typeof window !== "undefined";
  const isBrowserRemote =
    isBrowser &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1";

  // When loaded in a remote browser (e.g. deployed on Railway or Vercel)
  // and no public backend URL was provided (or it mistakenly still points to localhost),
  // fall back to relative path ("") so requests go to the Next.js origin,
  // which proxies them to the backend via next.config.ts rewrites!
  if (isBrowserRemote) {
    if (!envUrl || envUrl.includes("localhost") || envUrl.includes("127.0.0.1")) {
      return "";
    }
    return envUrl.replace(/\/$/, "");
  }

  // Local development or SSR fallback
  return envUrl ? envUrl.replace(/\/$/, "") : "http://localhost:8000";
})();

/**
 * Derive WebSocket URL from API base URL (http: -> ws:, https: -> wss:)
 */
export function getWsUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (API_BASE_URL) {
    const base = API_BASE_URL.replace(/^http:/, "ws:").replace(/^https:/, "wss:");
    return `${base}${normalizedPath}`;
  }
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${normalizedPath}`;
  }
  return `ws://localhost:8000${normalizedPath}`;
}

// ─── Token Storage ────────────────────────────────────────────────────────────

const TOKEN_KEY = "leadscout_jwt";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {}
}

export function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {}
}

// ─── Typed API Error ─────────────────────────────────────────────────────────

export class ApiError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(
    message: string,
    status = 500,
    code = "UNKNOWN_ERROR",
    details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

// ─── Route Map ───────────────────────────────────────────────────────────────

export const API_ROUTES = {
  // Auth
  signup: "/api/auth/signup",
  login: "/api/auth/login",
  me: "/api/auth/me",
  logout: "/api/auth/logout",
  forgotPassword: "/api/auth/forgot-password",
  resetPassword: "/api/auth/reset-password",

  // Users / Profile
  getProfile: "/api/users/me",
  updateProfile: "/api/users/me",
  changePassword: "/api/users/me/password",

  // Dashboard
  dashboardSummary: "/api/dashboard/summary",

  // Tasks
  createTask: "/api/scrape",
  getTasks: "/api/tasks",
  getTask: (taskId: string) => `/api/tasks/${encodeURIComponent(taskId)}`,
  getTaskLeads: (taskId: string) => `/api/tasks/${encodeURIComponent(taskId)}/leads`,
  exportTaskCsv: (taskId: string) => `/api/tasks/${encodeURIComponent(taskId)}/export/csv`,
  exportTaskExcel: (taskId: string) => `/api/tasks/${encodeURIComponent(taskId)}/export/excel`,

  // Leads
  getLeads: "/api/leads",
  getLead: (leadId: string) => `/api/leads/${encodeURIComponent(leadId)}`,
  deleteLeads: "/api/leads/delete",
  exportLeadsCsv: "/api/leads/export/csv",
  exportLeadsExcel: "/api/leads/export/excel",
  exportLeadCsv: (leadId: string) => `/api/leads/${encodeURIComponent(leadId)}/export/csv`,
  exportLeadExcel: (leadId: string) => `/api/leads/${encodeURIComponent(leadId)}/export/excel`,

  // WebSocket
  wsTask: (taskId: string) => `/api/ws/tasks/${encodeURIComponent(taskId)}`,
} as const;

/**
 * Build a full API URL from a route path.
 */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

// ─── Base Fetch Helper ────────────────────────────────────────────────────────

export interface FetchOptions extends RequestInit {
  /** Skip adding the Authorization header (e.g. for public login/signup calls). */
  skipAuth?: boolean;
  /** Request timeout in milliseconds (default: 30000ms). */
  timeoutMs?: number;
  /** Idempotency key header */
  idempotencyKey?: string;
}

/**
 * Centralized fetch wrapper that:
 *  - Appends Authorization: Bearer <token> when a token is stored.
 *  - Supports timeout via AbortController.
 *  - Handles 401 unauthenticated session expiry and clean client redirect.
 *  - Throws typed ApiError with parsed code, status, and message.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth, timeoutMs = 30000, idempotencyKey, ...init } = options;

  const headers = new Headers(init.headers);

  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (!skipAuth) {
    const token = getStoredToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (idempotencyKey) {
    headers.set("Idempotency-Key", idempotencyKey);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(apiUrl(path), {
      ...init,
      headers,
      signal: controller.signal,
      credentials: "include", // also send HttpOnly cookie when present
    });

    clearTimeout(timeoutId);

    // ─── 401 Session Handling ───────────────────────────────────────────────
    if (response.status === 401 && !skipAuth) {
      clearStoredToken();
      if (typeof window !== "undefined") {
        const currentPath = window.location.pathname;
        if (currentPath !== "/login" && currentPath !== "/signup") {
          window.dispatchEvent(new CustomEvent("leadscout:auth_expired"));
          // Soft redirect to login with destination
          setTimeout(() => {
            window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
          }, 100);
        }
      }
    }

    if (!response.ok) {
      let message = `Request failed (HTTP ${response.status})`;
      let code = "HTTP_ERROR";
      let details: unknown = undefined;

      try {
        const errorBody = await response.json();
        if (errorBody?.error) {
          code = errorBody.error.code ?? code;
          message = errorBody.error.message ?? message;
          details = errorBody.error.details;
        } else if (Array.isArray(errorBody?.detail)) {
          // FastAPI pydantic validation errors
          code = "VALIDATION_ERROR";
          message = errorBody.detail
            .map((d: { msg?: string; loc?: string[] }) => d.msg || "Invalid field")
            .join("; ");
          details = errorBody.detail;
        } else if (typeof errorBody?.detail === "string") {
          message = errorBody.detail;
          code = errorBody.code ?? code;
        } else if (errorBody?.message) {
          message = errorBody.message;
        }
      } catch {
        // Non-JSON response body
        if (response.statusText) {
          message = response.statusText;
        }
      }

      throw new ApiError(message, response.status, code, details);
    }

    // 204 No Content
    if (response.status === 204) return undefined as unknown as T;

    return response.json() as Promise<T>;
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    if ((error as Error)?.name === "AbortError") {
      throw new ApiError("Request timed out. Please try again.", 408, "TIMEOUT");
    }
    const rawMsg = (error as Error)?.message || "";
    const isFetchFailure =
      rawMsg.toLowerCase().includes("failed to fetch") ||
      rawMsg.toLowerCase().includes("networkerror") ||
      rawMsg.toLowerCase().includes("load failed");
    const userMessage = isFetchFailure
      ? "Unable to connect to the backend server. If deployed, please ensure the backend service is running and NEXT_PUBLIC_API_URL is configured."
      : rawMsg || "Network request failed. Please check your connection.";

    throw new ApiError(userMessage, 0, "NETWORK_ERROR");
  }
}

// ─── API Envelope Types ───────────────────────────────────────────────────────

export interface ApiSuccess<T> {
  success: true;
  data: T;
}

export interface BackendUser {
  id: string;
  name: string;
  email: string;
  company: string | null;
  role: "USER" | "ADMIN";
  avatar_url: string | null;
  created_at: string;
}

export interface TokenData {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: BackendUser;
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export interface SignupPayload {
  name: string;
  email: string;
  password: string;
  company?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UpdateProfilePayload {
  name?: string;
  company?: string;
  avatar_url?: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export const authApi = {
  async signup(data: SignupPayload): Promise<ApiSuccess<TokenData>> {
    return apiFetch<ApiSuccess<TokenData>>(API_ROUTES.signup, {
      method: "POST",
      body: JSON.stringify(data),
      skipAuth: true,
    });
  },

  async login(data: LoginPayload): Promise<ApiSuccess<TokenData>> {
    return apiFetch<ApiSuccess<TokenData>>(API_ROUTES.login, {
      method: "POST",
      body: JSON.stringify(data),
      skipAuth: true,
    });
  },

  async getMe(): Promise<ApiSuccess<BackendUser>> {
    return apiFetch<ApiSuccess<BackendUser>>(API_ROUTES.me);
  },

  async logout(): Promise<void> {
    try {
      await apiFetch(API_ROUTES.logout, { method: "POST" });
    } catch {
      // Ignore errors; token is cleared locally regardless
    }
    clearStoredToken();
  },

  async forgotPassword(email: string): Promise<ApiSuccess<{ message: string }>> {
    return apiFetch<ApiSuccess<{ message: string }>>(API_ROUTES.forgotPassword, {
      method: "POST",
      body: JSON.stringify({ email }),
      skipAuth: true,
    });
  },

  async resetPassword(
    token: string,
    new_password: string
  ): Promise<ApiSuccess<{ message: string }>> {
    return apiFetch<ApiSuccess<{ message: string }>>(API_ROUTES.resetPassword, {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
      skipAuth: true,
    });
  },

  async updateProfile(data: UpdateProfilePayload): Promise<ApiSuccess<BackendUser>> {
    return apiFetch<ApiSuccess<BackendUser>>(API_ROUTES.updateProfile, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async changePassword(data: ChangePasswordPayload): Promise<ApiSuccess<{ message: string }>> {
    return apiFetch<ApiSuccess<{ message: string }>>(API_ROUTES.changePassword, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};

// ─── Tasks API ────────────────────────────────────────────────────────────────

export interface CreateTaskPayload {
  location: string;
  keyword: string;
  search_radius?: number;
  max_results?: number;
  max_pages_per_site?: number;
  selected_fields?: string[];
  crawl_depth?: number;
  follow_internal_links?: boolean;
  prioritize_contact?: boolean;
  prioritize_about?: boolean;
  prioritize_admissions?: boolean;
  prioritize_staff_management?: boolean;
}

export interface BackendTaskResponse {
  task_id: string;
  status: string;
  location: string;
  keyword: string;
  max_results: number;
  max_pages_per_site: number;
  progress: number;
  queued: boolean;
  celery_task_id: string | null;
  created_at: string;
}

export interface BackendTaskListItem {
  task_id: string;
  keyword: string;
  location: string;
  status: string;
  progress: number;
  results_count: number;
  verified_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
}

export interface BackendTaskDetail {
  task_id: string;
  status: string;
  current_stage: string;
  progress: number;
  location: string;
  keyword: string;
  search_radius: number;
  max_results: number;
  max_pages_per_site: number;
  crawl_depth: number;
  selected_fields: string[];
  follow_internal_links: boolean;
  prioritize_contact: boolean;
  prioritize_about: boolean;
  prioritize_admissions: boolean;
  prioritize_staff_management: boolean;
  results_discovered: number;
  websites_found: number;
  websites_crawled: number;
  phones_found: number;
  emails_found: number;
  addresses_found: number;
  duplicates_removed: number;
  failed_websites: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  failure_reason: string | null;
}

export interface TaskPagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface PaginatedTasksResponse {
  success: boolean;
  data: BackendTaskListItem[];
  pagination: TaskPagination;
}

export interface TaskQueryParams {
  page?: number;
  limit?: number;
  status?: string;
  location?: string;
  keyword?: string;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export const tasksApi = {
  async createTask(
    payload: CreateTaskPayload,
    idempotencyKey?: string
  ): Promise<ApiSuccess<BackendTaskResponse>> {
    return apiFetch<ApiSuccess<BackendTaskResponse>>(API_ROUTES.createTask, {
      method: "POST",
      body: JSON.stringify(payload),
      idempotencyKey,
    });
  },

  async getTasks(params?: TaskQueryParams): Promise<PaginatedTasksResponse> {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.status) qs.set("status", params.status);
    if (params?.location) qs.set("location", params.location);
    if (params?.keyword) qs.set("keyword", params.keyword);
    if (params?.search) qs.set("keyword", params.search); // Search maps to keyword/location
    if (params?.sort_by) qs.set("sort_by", params.sort_by);
    if (params?.sort_order) qs.set("sort_order", params.sort_order);

    const query = qs.toString() ? `?${qs.toString()}` : "";
    return apiFetch<PaginatedTasksResponse>(`${API_ROUTES.getTasks}${query}`);
  },

  async getTask(taskId: string): Promise<ApiSuccess<BackendTaskDetail>> {
    return apiFetch<ApiSuccess<BackendTaskDetail>>(API_ROUTES.getTask(taskId));
  },
};

// ─── Dashboard API ────────────────────────────────────────────────────────────

export interface DashboardCategoryItem {
  category: string;
  leads: number;
  color?: string | null;
}

export interface DashboardLocationItem {
  location: string;
  leads: number;
}

export interface DashboardSummaryData {
  total_leads: number;
  websites_discovered: number;
  verified_leads: number;
  scraping_tasks: number;
  recent_tasks: BackendTaskListItem[];
  category_summary: DashboardCategoryItem[];
  location_summary: DashboardLocationItem[];
}

export const dashboardApi = {
  async getSummary(): Promise<ApiSuccess<DashboardSummaryData>> {
    return apiFetch<ApiSuccess<DashboardSummaryData>>(API_ROUTES.dashboardSummary);
  },
};
