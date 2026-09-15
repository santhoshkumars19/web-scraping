"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type { User, AuthState } from "@/types/auth";
import {
  authApi,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  type BackendUser,
} from "@/lib/api";

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Map backend snake_case UserResponse → frontend camelCase User */
function mapBackendUser(u: BackendUser): User {
  return {
    id: u.id,
    name: u.name,
    email: u.email,
    company: u.company ?? undefined,
    role: u.role as "USER" | "ADMIN",
    avatarUrl: u.avatar_url ?? undefined,
    createdAt: new Date(u.created_at).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }),
  };
}

// ─── Context Shape ────────────────────────────────────────────────────────────

interface AuthContextType extends AuthState {
  login: (
    email: string,
    pass: string,
    rememberMe?: boolean
  ) => Promise<{ success: boolean; error?: string }>;
  signup: (
    name: string,
    email: string,
    pass: string,
    company?: string
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  updateProfile: (updates: { name?: string; company?: string; avatarUrl?: string }) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<{ success: boolean; error?: string }>;
  deleteAccount: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: true,
  });

  // On mount: if we have a stored JWT, validate it by calling /api/auth/me
  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setAuthState({ isAuthenticated: false, user: null, isLoading: false });
      return;
    }

    authApi
      .getMe()
      .then((res) => {
        setAuthState({
          isAuthenticated: true,
          user: mapBackendUser(res.data),
          isLoading: false,
        });
      })
      .catch(() => {
        // Token invalid / expired — clear it
        clearStoredToken();
        setAuthState({ isAuthenticated: false, user: null, isLoading: false });
      });
  }, []);

  // ─── login ────────────────────────────────────────────────────────────────

  const login = useCallback(
    async (email: string, pass: string, rememberMe?: boolean) => {
      try {
        const res = await authApi.login({ email, password: pass });
        const { access_token, user } = res.data;
        setStoredToken(access_token);

        // "Remember me" — nothing extra needed; the JWT persists in localStorage
        // until explicit logout regardless. If rememberMe is false, nothing changes
        // in this simple implementation (session-length control is server-side via exp).
        void rememberMe; // suppress unused-var warning

        const mappedUser = mapBackendUser(user);
        setAuthState({ isAuthenticated: true, user: mappedUser, isLoading: false });
        toast.success("Signed in successfully.", {
          description: `Welcome back, ${mappedUser.name}.`,
        });
        return { success: true };
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Invalid email or password.";
        return { success: false, error: message };
      }
    },
    []
  );

  // ─── signup ───────────────────────────────────────────────────────────────

  const signup = useCallback(
    async (name: string, email: string, pass: string, company?: string) => {
      try {
        const res = await authApi.signup({ name, email, password: pass, company });
        const { access_token, user } = res.data;
        setStoredToken(access_token);

        const mappedUser = mapBackendUser(user);
        setAuthState({ isAuthenticated: true, user: mappedUser, isLoading: false });
        toast.success("Account created successfully.", {
          description: "Welcome to LeadScout!",
        });
        return { success: true };
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to create account.";
        return { success: false, error: message };
      }
    },
    []
  );

  // ─── logout ───────────────────────────────────────────────────────────────

  const logout = useCallback(() => {
    authApi.logout(); // fire-and-forget (also clears localStorage token)
    setAuthState({ isAuthenticated: false, user: null, isLoading: false });
    toast.success("You've been logged out.");
    router.push("/login");
  }, [router]);

  // ─── updateProfile ────────────────────────────────────────────────────────

  const updateProfile = useCallback(
    async (updates: { name?: string; company?: string; avatarUrl?: string }) => {
      try {
        const res = await authApi.updateProfile({
          name: updates.name,
          company: updates.company,
          avatar_url: updates.avatarUrl,
        });
        const mappedUser = mapBackendUser(res.data);
        setAuthState((prev) => ({ ...prev, user: mappedUser }));
        toast.success("Profile updated.");
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to update profile.";
        toast.error("Profile update failed.", { description: message });
      }
    },
    []
  );

  // ─── changePassword ───────────────────────────────────────────────────────

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      try {
        await authApi.changePassword({
          current_password: currentPassword,
          new_password: newPassword,
        });
        toast.success("Password changed successfully.");
        return { success: true };
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to change password.";
        return { success: false, error: message };
      }
    },
    []
  );

  // ─── deleteAccount ────────────────────────────────────────────────────────

  const deleteAccount = useCallback(() => {
    authApi.logout();
    setAuthState({ isAuthenticated: false, user: null, isLoading: false });
    toast.success("Account deleted.", {
      description: "Your account has been removed.",
    });
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        signup,
        logout,
        updateProfile,
        changePassword,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
