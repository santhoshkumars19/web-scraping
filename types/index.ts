// ============================================================
// LeadScout — Shared TypeScript Types
// ============================================================

// --- Task ---

export type TaskStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "PAUSED" | "CANCELLED";

export interface ScrapingTask {
  id: string;
  taskId: string; // e.g. TASK-000124
  location: string;
  keyword: string;
  maxResults: number;
  maxPagesPerSite: number;
  requiredFields: RequiredField[];
  status: TaskStatus;
  progress: number; // 0–100
  stats: TaskStats;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export type RequiredField =
  | "name"
  | "phone"
  | "email"
  | "website"
  | "address"
  | "whatsapp"
  | "social_links"
  | "contact_person";

export interface TaskStats {
  discovered: number;
  websitesFound: number;
  websitesCrawled: number;
  phonesFound: number;
  emailsFound: number;
  addressesFound: number;
  duplicatesRemoved: number;
}

// --- Lead / Organization ---

export type DataConfidence = "HIGH" | "MEDIUM" | "LOW";

export interface Lead {
  id: string;
  taskId: string;
  name: string;
  category: string;
  location: string;
  city?: string;
  state?: string;
  pincode?: string;
  address?: string;

  // Contact
  phone?: string;
  alternatePhone?: string;
  email?: string;
  website?: string;
  whatsapp?: string;
  contactPerson?: string;
  designation?: string;

  // Social
  facebook?: string;
  instagram?: string;
  linkedin?: string;
  youtube?: string;
  otherSocialLinks?: string[];

  // Metadata
  sourceUrl?: string;
  confidence: DataConfidence;
  verification: VerificationStatus;
  scrapedAt: string;
}

export interface VerificationStatus {
  phone: boolean;
  email: boolean;
  website: boolean;
  address: boolean;
  contactPerson: boolean;
}

// --- User ---

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  role: "admin" | "user";
}

// --- Navigation ---

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

export interface NavGroup {
  label?: string;
  items: NavItem[];
}
