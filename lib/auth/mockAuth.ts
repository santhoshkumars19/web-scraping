// ============================================================
// LeadScout — Mock Authentication Service & Storage
// ============================================================

import type {
  User,
  UserPreferences,
  NotificationPreferences,
  ApiKeyInfo,
} from "@/types/auth";

export const AUTH_STORAGE_KEY = "leadscout_auth";
export const PREFERENCES_STORAGE_KEY = "leadscout_preferences";
export const NOTIFICATIONS_STORAGE_KEY = "leadscout_notifications";
export const API_KEY_STORAGE_KEY = "leadscout_api_key";
export const REMEMBER_EMAIL_KEY = "leadscout_remember_email";

/**
 * Default mock user configuration
 */
export const DEFAULT_MOCK_USER: User = {
  id: "user-001",
  name: "Demo User",
  email: "demo@leadscout.app",
  company: "LeadScout Demo",
  role: "ADMIN",
  createdAt: "Sep 01, 2026",
};

/**
 * Default workspace preferences
 */
export const DEFAULT_PREFERENCES: UserPreferences = {
  theme: "system",
  language: "English",
  defaultLocation: "Puducherry",
  defaultSearchRadius: 25,
  defaultMaxResults: 100,
  defaultPagesPerWebsite: 20,
  defaultExportFormat: "csv",
};

/**
 * Default notification settings
 */
export const DEFAULT_NOTIFICATIONS: NotificationPreferences = {
  taskCompleted: true,
  taskFailed: true,
  exportCompleted: true,
  systemUpdates: false,
};

/**
 * Load mock authentication status
 */
export function getStoredAuth(): { isAuthenticated: boolean; user: User | null } {
  if (typeof window === "undefined") {
    return { isAuthenticated: false, user: null };
  }

  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed.isAuthenticated && parsed.user) {
        return { isAuthenticated: true, user: parsed.user };
      }
    }
  } catch {}

  return { isAuthenticated: false, user: null };
}

/**
 * Save mock authentication status to localStorage
 */
export function saveStoredAuth(user: User | null): void {
  if (typeof window === "undefined") return;

  try {
    if (user) {
      localStorage.setItem(
        AUTH_STORAGE_KEY,
        JSON.stringify({ isAuthenticated: true, user })
      );
    } else {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  } catch {}
}

/**
 * Mock Login
 * Valid credentials: demo@leadscout.app / LeadScout123
 */
export async function mockLogin(
  email: string,
  pass: string,
  rememberMe?: boolean
): Promise<{ success: boolean; user?: User; error?: string }> {
  // Simulate network latency
  await new Promise((res) => setTimeout(res, 400));

  const cleanEmail = email.trim().toLowerCase();

  if (rememberMe && typeof window !== "undefined") {
    localStorage.setItem(REMEMBER_EMAIL_KEY, cleanEmail);
  } else if (typeof window !== "undefined") {
    localStorage.removeItem(REMEMBER_EMAIL_KEY);
  }

  // Check demo credentials or match local saved user
  const stored = getStoredAuth();
  const isMatch =
    (cleanEmail === "demo@leadscout.app" && pass === "LeadScout123") ||
    (stored.user && cleanEmail === stored.user.email.toLowerCase());

  if (!isMatch) {
    return {
      success: false,
      error: "Invalid email or password.",
    };
  }

  const activeUser = stored.user || DEFAULT_MOCK_USER;
  saveStoredAuth(activeUser);

  return {
    success: true,
    user: activeUser,
  };
}

/**
 * Mock Sign Up
 */
export async function mockSignup(
  name: string,
  email: string,
  _pass: string
): Promise<{ success: boolean; user?: User; error?: string }> {
  await new Promise((res) => setTimeout(res, 500));

  const newUser: User = {
    id: `user-${Date.now().toString(36)}`,
    name: name.trim(),
    email: email.trim().toLowerCase(),
    company: "LeadScout Workspace",
    role: "USER",
    createdAt: new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }),
  };

  saveStoredAuth(newUser);

  return {
    success: true,
    user: newUser,
  };
}

/**
 * Mock Logout
 */
export function mockLogout(): void {
  saveStoredAuth(null);
}

/**
 * Update mock user profile
 */
export function mockUpdateProfile(updates: Partial<User>): User | null {
  const current = getStoredAuth();
  if (!current.user) return null;

  const updated: User = {
    ...current.user,
    ...updates,
    email: current.user.email, // Email remains fixed
  };

  saveStoredAuth(updated);
  return updated;
}

/**
 * Preferences Storage
 */
export function loadPreferences(): UserPreferences {
  if (typeof window === "undefined") return DEFAULT_PREFERENCES;
  try {
    const raw = localStorage.getItem(PREFERENCES_STORAGE_KEY);
    if (raw) return { ...DEFAULT_PREFERENCES, ...JSON.parse(raw) };
  } catch {}
  return DEFAULT_PREFERENCES;
}

export function savePreferences(prefs: UserPreferences): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(prefs));
  } catch {}
}

/**
 * Notification Settings Storage
 */
export function loadNotificationPreferences(): NotificationPreferences {
  if (typeof window === "undefined") return DEFAULT_NOTIFICATIONS;
  try {
    const raw = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
    if (raw) return { ...DEFAULT_NOTIFICATIONS, ...JSON.parse(raw) };
  } catch {}
  return DEFAULT_NOTIFICATIONS;
}

export function saveNotificationPreferences(
  notifs: NotificationPreferences
): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifs));
  } catch {}
}

/**
 * API Key Storage & Generation
 */
export function loadApiKeyInfo(): ApiKeyInfo {
  const fallbackKey = "ls_live_948f2a1b0c8d7e6f5a4b3c2d1e0f";
  if (typeof window === "undefined") {
    return {
      key: fallbackKey,
      maskedKey: "ls_live_••••••••••••••••",
      createdAt: "Sep 01, 2026",
      lastUsed: "2 hours ago",
    };
  }

  try {
    const raw = localStorage.getItem(API_KEY_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}

  const defaultKey: ApiKeyInfo = {
    key: fallbackKey,
    maskedKey: "ls_live_••••••••••••••••",
    createdAt: "Sep 01, 2026",
    lastUsed: "2 hours ago",
  };
  localStorage.setItem(API_KEY_STORAGE_KEY, JSON.stringify(defaultKey));
  return defaultKey;
}

export function regenerateApiKey(): ApiKeyInfo {
  const randomHex = Array.from({ length: 28 }, () =>
    Math.floor(Math.random() * 16).toString(16)
  ).join("");
  const newKey = `ls_live_${randomHex}`;

  const info: ApiKeyInfo = {
    key: newKey,
    maskedKey: "ls_live_••••••••••••••••",
    createdAt: "Just now",
    lastUsed: "Never",
  };

  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(API_KEY_STORAGE_KEY, JSON.stringify(info));
    } catch {}
  }

  return info;
}
