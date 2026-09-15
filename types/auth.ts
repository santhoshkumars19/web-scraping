// ============================================================
// LeadScout — Authentication & Settings Types
// ============================================================

export type UserRole = "USER" | "ADMIN";

export interface User {
  id: string;
  name: string;
  email: string;
  company?: string;
  role: UserRole;
  avatarUrl?: string;
  createdAt: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
}

export interface UserPreferences {
  theme: "system" | "light" | "dark";
  language: string;
  defaultLocation: string;
  defaultSearchRadius: number;
  defaultMaxResults: number;
  defaultPagesPerWebsite: number;
  defaultExportFormat: "csv" | "excel";
}

export interface NotificationPreferences {
  taskCompleted: boolean;
  taskFailed: boolean;
  exportCompleted: boolean;
  systemUpdates: boolean;
}

export interface ApiKeyInfo {
  key: string;
  maskedKey: string;
  createdAt: string;
  lastUsed: string;
}
