import type { User } from "@/types";

/**
 * Mock authenticated user for UI development.
 * Replace with real auth data when authentication is implemented.
 */
export const mockUser: User = {
  id: "usr_001",
  name: "Alex Johnson",
  email: "alex@leadscout.app",
  avatarUrl: undefined,
  role: "admin",
};
