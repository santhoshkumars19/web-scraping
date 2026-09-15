// ============================================================
// LeadScout — Export Utilities & Field Definitions
// ============================================================

import type { Lead } from "@/types/lead";
import type {
  ExportFieldId,
  ExportFieldDefinition,
  ExportFieldGroup,
} from "@/types/export";

/**
 * All exportable field definitions with metadata and grouping
 */
export const EXPORT_FIELD_DEFINITIONS: ExportFieldDefinition[] = [
  // ── ORGANIZATION ──
  {
    id: "organizationName",
    label: "Organization Name",
    defaultSelected: true,
    group: "ORGANIZATION",
  },
  {
    id: "category",
    label: "Category",
    defaultSelected: true,
    group: "ORGANIZATION",
  },
  {
    id: "website",
    label: "Website",
    defaultSelected: true,
    group: "ORGANIZATION",
  },

  // ── LOCATION ──
  {
    id: "address",
    label: "Address",
    defaultSelected: true,
    group: "LOCATION",
  },
  {
    id: "city",
    label: "City",
    defaultSelected: true,
    group: "LOCATION",
  },
  {
    id: "state",
    label: "State",
    defaultSelected: true,
    group: "LOCATION",
  },
  {
    id: "pincode",
    label: "Pincode",
    defaultSelected: true,
    group: "LOCATION",
  },

  // ── CONTACT ──
  {
    id: "phone",
    label: "Phone",
    defaultSelected: true,
    group: "CONTACT",
  },
  {
    id: "alternatePhone",
    label: "Alternate Phone",
    defaultSelected: false,
    group: "CONTACT",
  },
  {
    id: "email",
    label: "Email",
    defaultSelected: true,
    group: "CONTACT",
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    defaultSelected: true,
    group: "CONTACT",
  },
  {
    id: "contactPerson",
    label: "Contact Person",
    defaultSelected: true,
    group: "CONTACT",
  },
  {
    id: "designation",
    label: "Designation",
    defaultSelected: true,
    group: "CONTACT",
  },

  // ── ONLINE PRESENCE ──
  {
    id: "facebook",
    label: "Facebook",
    defaultSelected: false,
    group: "ONLINE PRESENCE",
  },
  {
    id: "instagram",
    label: "Instagram",
    defaultSelected: false,
    group: "ONLINE PRESENCE",
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    defaultSelected: false,
    group: "ONLINE PRESENCE",
  },
  {
    id: "youtube",
    label: "YouTube",
    defaultSelected: false,
    group: "ONLINE PRESENCE",
  },
  {
    id: "otherSocial",
    label: "Other Social Links",
    defaultSelected: false,
    group: "ONLINE PRESENCE",
  },

  // ── DATA QUALITY ──
  {
    id: "verification",
    label: "Verification",
    defaultSelected: true,
    group: "DATA QUALITY",
  },
  {
    id: "scrapedDate",
    label: "Scraped Date",
    defaultSelected: true,
    group: "DATA QUALITY",
  },
  {
    id: "taskId",
    label: "Task ID",
    defaultSelected: true,
    group: "DATA QUALITY",
  },
  {
    id: "sourceUrls",
    label: "Source URLs",
    defaultSelected: false,
    group: "DATA QUALITY",
  },
];

/**
 * Grouped field definitions for UI accordion/sections
 */
export const EXPORT_FIELD_GROUPS: ExportFieldGroup[] = [
  {
    groupKey: "ORGANIZATION",
    title: "Organization",
    fields: EXPORT_FIELD_DEFINITIONS.filter((f) => f.group === "ORGANIZATION"),
  },
  {
    groupKey: "LOCATION",
    title: "Location",
    fields: EXPORT_FIELD_DEFINITIONS.filter((f) => f.group === "LOCATION"),
  },
  {
    groupKey: "CONTACT",
    title: "Contact",
    fields: EXPORT_FIELD_DEFINITIONS.filter((f) => f.group === "CONTACT"),
  },
  {
    groupKey: "ONLINE PRESENCE",
    title: "Online Presence",
    fields: EXPORT_FIELD_DEFINITIONS.filter((f) => f.group === "ONLINE PRESENCE"),
  },
  {
    groupKey: "DATA QUALITY",
    title: "Data Quality",
    fields: EXPORT_FIELD_DEFINITIONS.filter((f) => f.group === "DATA QUALITY"),
  },
];

/**
 * Canonical predictable column order
 */
export const ORDERED_EXPORT_FIELDS: ExportFieldId[] = EXPORT_FIELD_DEFINITIONS.map(
  (f) => f.id
);

/**
 * Default selection of 15 fields
 */
export const DEFAULT_SELECTED_FIELDS: ExportFieldId[] = EXPORT_FIELD_DEFINITIONS.filter(
  (f) => f.defaultSelected
).map((f) => f.id);

/**
 * Sort selected fields to guarantee predictable output column order
 */
export function sortFieldsToPredictableOrder(
  selectedFieldIds: ExportFieldId[]
): ExportFieldId[] {
  const set = new Set(selectedFieldIds);
  return ORDERED_EXPORT_FIELDS.filter((id) => set.has(id));
}

/**
 * Get readable label for field ID
 */
export function getFieldLabel(id: ExportFieldId): string {
  const found = EXPORT_FIELD_DEFINITIONS.find((f) => f.id === id);
  return found ? found.label : id;
}

/**
 * Extract clean string representation for a lead field
 */
export function getLeadFieldValue(lead: Lead, fieldId: ExportFieldId): string {
  switch (fieldId) {
    case "organizationName":
      return lead.organizationName || "";
    case "category":
      return lead.category || "";
    case "website":
      return lead.website || "";
    case "address":
      return lead.address || "";
    case "city":
      return lead.city || "";
    case "state":
      return lead.state || "";
    case "pincode":
      return lead.pincode || "";
    case "phone":
      return lead.phone || "";
    case "alternatePhone":
      return lead.alternatePhone || "";
    case "email":
      return lead.email || "";
    case "whatsapp":
      return lead.whatsapp || "";
    case "contactPerson":
      return lead.contactPerson || "";
    case "designation":
      return lead.designation || "";
    case "facebook":
      return (
        lead.socialLinks?.find((s) => s.platform === "facebook")?.url || ""
      );
    case "instagram":
      return (
        lead.socialLinks?.find((s) => s.platform === "instagram")?.url || ""
      );
    case "linkedin":
      return (
        lead.socialLinks?.find((s) => s.platform === "linkedin")?.url || ""
      );
    case "youtube":
      return (
        lead.socialLinks?.find((s) => s.platform === "youtube")?.url || ""
      );
    case "otherSocial":
      return (
        lead.socialLinks
          ?.filter(
            (s) =>
              !["facebook", "instagram", "linkedin", "youtube"].includes(
                s.platform
              )
          )
          .map((s) => s.url)
          .filter(Boolean)
          .join("; ") || ""
      );
    case "verification":
      return lead.verification
        ? `${lead.verification.status} (${lead.verification.fieldsFound}/${lead.verification.totalFields})`
        : "";
    case "scrapedDate":
      return lead.scrapedDate || "";
    case "taskId":
      return lead.taskId || "";
    case "sourceUrls":
      return (
        lead.sourcePages
          ?.map((p) => p.url)
          .filter(Boolean)
          .join("; ") || ""
      );
    default:
      return "";
  }
}

/**
 * Sanitize filename to ensure safe browser downloads
 */
export function sanitizeFileName(name: string, fallback = "leadscout-leads"): string {
  if (!name || !name.trim()) {
    const today = new Date().toISOString().split("T")[0];
    return `${fallback}-${today}`;
  }

  // Remove illegal characters: < > : " / \ | ? * and control chars
  let cleaned = name
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^\.+|\.+$/g, ""); // remove leading/trailing dots

  // Strip known extensions if user typed them in
  cleaned = cleaned.replace(/\.(csv|xlsx|xls)$/i, "");

  if (!cleaned) {
    const today = new Date().toISOString().split("T")[0];
    return `${fallback}-${today}`;
  }

  return cleaned;
}

/**
 * Generate default filename based on context
 */
export function generateDefaultFileName(context?: {
  singleLeadName?: string;
  taskId?: string;
}): string {
  const today = new Date().toISOString().split("T")[0];

  if (context?.singleLeadName) {
    const safeName = context.singleLeadName
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "-")
      .replace(/-+/g, "-")
      .slice(0, 30);
    return `leadscout-${safeName}-${today}`;
  }

  if (context?.taskId) {
    const safeTask = context.taskId.toLowerCase();
    return `leadscout-${safeTask}-${today}`;
  }

  return `leadscout-leads-${today}`;
}

/**
 * Helper to trigger browser download of a Blob
 */
export function downloadBlob(blob: Blob, fullFileName: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fullFileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Revoke object URL after brief delay
  setTimeout(() => URL.revokeObjectURL(url), 15000);
}
