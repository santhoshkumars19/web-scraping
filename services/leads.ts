/**
 * services/leads.ts
 *
 * REST API client service for Lead management, queries, filtering, and details.
 * Communicates with the FastAPI backend and maps API DTOs into frontend types.
 */

import { apiFetch, API_ROUTES } from "@/lib/api";
import type {
  Lead,
  DataConfidence,
  SocialLink,
  SourcePage,
  Verification,
  LeadSortField,
  SortDirection,
} from "@/types/lead";

// ── Backend DTO Interfaces ───────────────────────────────────────────────────

interface BackendLeadOrg {
  id: string;
  name: string;
  category?: string | null;
  website?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
}

interface BackendVerificationSummary {
  status: string;
  score: number;
  fields_found: number;
  total_fields: number;
}

interface BackendVerificationDetail extends BackendVerificationSummary {
  completeness_percentage: number;
  source_quality_score: number;
  consistency_score: number;
  reasons: Record<string, any>;
  source_quality_details: Record<string, any>;
  verified_at?: string | null;
}

interface BackendPhone {
  id: string;
  number: string;
  normalized_number: string;
  type: string;
  is_primary: boolean;
  is_whatsapp: boolean;
}

interface BackendEmail {
  id: string;
  email: string;
  normalized_email: string;
  type: string;
  is_primary: boolean;
}

interface BackendContact {
  id: string;
  name: string;
  designation?: string | null;
}

interface BackendSocialLink {
  platform: string;
  url: string;
  is_official: boolean;
}

interface BackendWebsite {
  id: string;
  url: string;
  domain?: string | null;
  is_official: boolean;
}

interface BackendSourceRecord {
  field: string;
  value: string;
  source_url: string;
  page_type?: string | null;
  page_title?: string | null;
}

interface BackendLeadListItem {
  id: string;
  task_id: string;
  organization: BackendLeadOrg;
  phone?: string | null;
  alternate_phone?: string | null;
  whatsapp?: string | null;
  email?: string | null;
  website?: string | null;
  location?: string | null;
  contact_person?: string | null;
  designation?: string | null;
  verification: BackendVerificationSummary;
  scraped_date: string;
}

interface BackendLeadDetail {
  id: string;
  task_id: string;
  task?: {
    task_id: string;
    keyword: string;
    location: string;
    status: string;
    created_at: string;
    completed_at?: string | null;
  } | null;
  organization: BackendLeadOrg;
  websites: BackendWebsite[];
  phones: BackendPhone[];
  emails: BackendEmail[];
  contacts: BackendContact[];
  social_links: BackendSocialLink[];
  sources: BackendSourceRecord[];
  verification: BackendVerificationDetail;
  scraped_date: string;
}

interface BackendPagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

interface BackendListEnvelope {
  success: boolean;
  data: BackendLeadListItem[];
  pagination: BackendPagination;
}

interface BackendDetailEnvelope {
  success: boolean;
  data: BackendLeadDetail;
}

// ── Public Service Types ─────────────────────────────────────────────────────

export interface LeadQueryParams {
  taskId?: string;
  page?: number;
  limit?: number;
  search?: string;
  category?: string;
  location?: string;
  verification?: DataConfidence | "PENDING";
  hasPhone?: boolean;
  hasEmail?: boolean;
  hasWebsite?: boolean;
  hasWhatsApp?: boolean;
  hasContactPerson?: boolean;
  hasSocialLinks?: boolean;
  scrapedFrom?: string;
  scrapedTo?: string;
  sortBy?: "organization" | "category" | "location" | "verification" | "scraped_date";
  sortOrder?: "asc" | "desc";
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface PaginatedLeadsResult {
  data: Lead[];
  pagination: PaginationMeta;
}

// ── Model Transformation Mappers ─────────────────────────────────────────────

function formatDate(isoString: string): string {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return isoString;
  }
}

function mapBackendListItemToLead(item: BackendLeadListItem): Lead {
  const org = item.organization;
  const location =
    item.location ||
    [org?.city, org?.state].filter(Boolean).join(", ") ||
    "";

  return {
    id: item.id,
    organizationName: org?.name ?? "Unknown",
    category: org?.category ?? "General",
    location,
    phone: item.phone ?? undefined,
    alternatePhone: item.alternate_phone ?? undefined,
    email: item.email ?? undefined,
    website: item.website ?? org?.website ?? undefined,
    address: org?.address ?? undefined,
    city: org?.city ?? undefined,
    state: org?.state ?? undefined,
    pincode: org?.pincode ?? undefined,
    whatsapp: item.whatsapp ?? undefined,
    contactPerson: item.contact_person ?? undefined,
    designation: item.designation ?? undefined,
    verification: {
      status: (item.verification?.status as DataConfidence) ?? "LOW",
      fieldsFound: item.verification?.fields_found ?? 0,
      totalFields: item.verification?.total_fields ?? 0,
    },
    scrapedDate: formatDate(item.scraped_date),
    taskId: item.task_id ?? "",
  };
}

function mapBackendDetailToLead(item: BackendLeadDetail): Lead {
  const org = item.organization;
  const primaryPhone =
    item.phones?.find((p) => p.is_primary)?.number ?? item.phones?.[0]?.number;
  const alternatePhone = item.phones?.find(
    (p) => p.number !== primaryPhone
  )?.number;
  const whatsappPhone = item.phones?.find((p) => p.is_whatsapp)?.number;
  const primaryEmail =
    item.emails?.find((e) => e.is_primary)?.email ?? item.emails?.[0]?.email;
  const primaryContact = item.contacts?.[0];

  const socialLinks: SocialLink[] = (item.social_links ?? []).map((s) => ({
    platform: (s.platform.toLowerCase() as SocialLink["platform"]) || "other",
    url: s.url,
  }));

  const sourcePages: SourcePage[] = (item.sources ?? []).map((s) => ({
    field: s.field,
    url: s.source_url,
    pageTitle: s.page_title ?? undefined,
  }));

  const location =
    [org?.city, org?.state].filter(Boolean).join(", ") || "";

  return {
    id: item.id,
    organizationName: org?.name ?? "Unknown",
    category: org?.category ?? "General",
    location,
    phone: primaryPhone,
    alternatePhone,
    email: primaryEmail,
    website: org?.website ?? item.websites?.[0]?.url,
    address: org?.address ?? undefined,
    city: org?.city ?? undefined,
    state: org?.state ?? undefined,
    pincode: org?.pincode ?? undefined,
    whatsapp: whatsappPhone,
    contactPerson: primaryContact?.name,
    designation: primaryContact?.designation ?? undefined,
    socialLinks: socialLinks.length > 0 ? socialLinks : undefined,
    sourcePages: sourcePages.length > 0 ? sourcePages : undefined,
    verification: {
      status: (item.verification?.status as DataConfidence) ?? "LOW",
      fieldsFound: item.verification?.fields_found ?? 0,
      totalFields: item.verification?.total_fields ?? 0,
      score: item.verification?.score ?? 0,
      completenessPercentage: item.verification?.completeness_percentage ?? 0,
      sourceQualityScore: item.verification?.source_quality_score ?? 0,
      consistencyScore: item.verification?.consistency_score ?? 0,
      reasons: item.verification?.reasons,
      verifiedAt: item.verification?.verified_at,
    },
    scrapedDate: formatDate(item.scraped_date),
    taskId: item.task_id ?? "",
  };
}

// ── Query String Builder ─────────────────────────────────────────────────────

function buildQueryParams(params?: LeadQueryParams): string {
  if (!params) return "";
  const query = new URLSearchParams();

  if (params.page !== undefined) query.set("page", String(params.page));
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.search?.trim()) query.set("search", params.search.trim());
  if (params.category?.trim()) query.set("category", params.category.trim());
  if (params.location?.trim()) query.set("location", params.location.trim());
  if (params.verification) query.set("verification", params.verification);
  if (params.hasPhone !== undefined) query.set("has_phone", String(params.hasPhone));
  if (params.hasEmail !== undefined) query.set("has_email", String(params.hasEmail));
  if (params.hasWebsite !== undefined) query.set("has_website", String(params.hasWebsite));
  if (params.hasWhatsApp !== undefined) query.set("has_whatsapp", String(params.hasWhatsApp));
  if (params.hasContactPerson !== undefined) query.set("has_contact", String(params.hasContactPerson));
  if (params.hasSocialLinks !== undefined) query.set("has_social", String(params.hasSocialLinks));
  if (params.scrapedFrom) query.set("scraped_from", params.scrapedFrom);
  if (params.scrapedTo) query.set("scraped_to", params.scrapedTo);
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.sortOrder) query.set("sort_order", params.sortOrder);
  if (params.taskId?.trim()) query.set("task_id", params.taskId.trim());

  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

// ── API Methods ──────────────────────────────────────────────────────────────

/**
 * Fetch global paginated leads with filters and search.
 */
export async function getLeads(params?: LeadQueryParams): Promise<PaginatedLeadsResult> {
  const qs = buildQueryParams(params);
  const json = await apiFetch<BackendListEnvelope>(`${API_ROUTES.getLeads}${qs}`);
  return {
    data: (json.data ?? []).map(mapBackendListItemToLead),
    pagination: {
      page: json.pagination.page,
      limit: json.pagination.limit,
      total: json.pagination.total,
      totalPages: json.pagination.total_pages,
      hasNext: json.pagination.has_next,
      hasPrev: json.pagination.has_prev,
    },
  };
}

/**
 * Fetch paginated leads scoped to a specific task.
 */
export async function getTaskLeads(
  taskId: string,
  params?: LeadQueryParams
): Promise<PaginatedLeadsResult> {
  const qs = buildQueryParams(params);
  const json = await apiFetch<BackendListEnvelope>(`${API_ROUTES.getTaskLeads(taskId)}${qs}`);
  return {
    data: (json.data ?? []).map(mapBackendListItemToLead),
    pagination: {
      page: json.pagination.page,
      limit: json.pagination.limit,
      total: json.pagination.total,
      totalPages: json.pagination.total_pages,
      hasNext: json.pagination.has_next,
      hasPrev: json.pagination.has_prev,
    },
  };
}

/**
 * Fetch full details, contacts, sources, and verification for a single lead.
 */
export async function getLead(leadId: string): Promise<Lead> {
  const json = await apiFetch<BackendDetailEnvelope>(API_ROUTES.getLead(leadId));
  return mapBackendDetailToLead(json.data);
}
