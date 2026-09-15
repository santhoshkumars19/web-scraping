export type DataConfidence = "HIGH" | "MEDIUM" | "LOW";

export interface SocialLink {
  platform: "facebook" | "instagram" | "linkedin" | "youtube" | "twitter" | "other";
  url: string;
}

export interface SourcePage {
  field: string;
  url: string;
  pageTitle?: string;
}

export interface Verification {
  status: DataConfidence;
  fieldsFound: number;
  totalFields: number;
  score?: number;
  completenessPercentage?: number;
  sourceQualityScore?: number;
  consistencyScore?: number;
  reasons?: Record<string, unknown>;
  verifiedAt?: string | null;
}

export interface Lead {
  id: string;
  organizationName: string;
  category: string;
  location: string;
  phone?: string;
  alternatePhone?: string;
  email?: string;
  website?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  whatsapp?: string;
  contactPerson?: string;
  designation?: string;
  socialLinks?: SocialLink[];
  sourcePages?: SourcePage[];
  verification: Verification;
  scrapedDate: string;
  taskId: string;
}

export interface LeadFilterState {
  search: string;
  categories: string[];
  locations: string[];
  verifications: DataConfidence[];
  hasPhone: boolean;
  hasEmail: boolean;
  hasWebsite: boolean;
  hasWhatsApp: boolean;
  hasContactPerson: boolean;
  hasSocialLinks: boolean;
  taskId: string;
  dateRange: "all" | "today" | "7d" | "30d" | "custom";
}

export type LeadSortField =
  | "organizationName"
  | "location"
  | "category"
  | "verification"
  | "scrapedDate";

export type SortDirection = "asc" | "desc";

export interface ColumnVisibilityState {
  organization: boolean;
  category: boolean;
  location: boolean;
  phone: boolean;
  email: boolean;
  website: boolean;
  address: boolean;
  whatsapp: boolean;
  contactPerson: boolean;
  verification: boolean;
  scrapedDate: boolean;
}
