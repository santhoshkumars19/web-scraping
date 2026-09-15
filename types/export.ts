// ============================================================
// LeadScout — Export Types
// ============================================================

import type { Lead } from "./lead";

export type ExportFormat = "csv" | "excel";

export type ExportStatus = "COMPLETED" | "FAILED";

export type ExportSourceType =
  | "ALL_LEADS"
  | "FILTERED_LEADS"
  | "SELECTED_LEADS"
  | "TASK"
  | "SINGLE_LEAD";

export type ExportFieldId =
  // ORGANIZATION
  | "organizationName"
  | "category"
  | "website"
  // LOCATION
  | "address"
  | "city"
  | "state"
  | "pincode"
  // CONTACT
  | "phone"
  | "alternatePhone"
  | "email"
  | "whatsapp"
  | "contactPerson"
  | "designation"
  // ONLINE PRESENCE
  | "facebook"
  | "instagram"
  | "linkedin"
  | "youtube"
  | "otherSocial"
  // DATA QUALITY
  | "verification"
  | "scrapedDate"
  | "taskId"
  | "sourceUrls";

export interface ExportFieldDefinition {
  id: ExportFieldId;
  label: string;
  defaultSelected: boolean;
  group: "ORGANIZATION" | "LOCATION" | "CONTACT" | "ONLINE PRESENCE" | "DATA QUALITY";
}

export interface ExportFieldGroup {
  groupKey: "ORGANIZATION" | "LOCATION" | "CONTACT" | "ONLINE PRESENCE" | "DATA QUALITY";
  title: string;
  fields: ExportFieldDefinition[];
}

export interface ExportRecord {
  id: string;
  fileName: string;
  format: ExportFormat;
  recordCount: number;
  createdAt: string;
  status: ExportStatus;
  taskId?: string;
  sourceType: ExportSourceType;
  fileSize?: string;
  blobUrl?: string; // Cache in memory for instant re-download
}

export interface ExportOptions {
  leads: Lead[];
  format: ExportFormat;
  fieldIds: ExportFieldId[];
  fileName: string;
  sourceType: ExportSourceType;
  taskId?: string;
}

export interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  // Leads context
  allLeads?: Lead[];
  filteredLeads?: Lead[];
  selectedLeads?: Lead[];
  // Direct presets
  initialSourceType?: ExportSourceType;
  initialFormat?: ExportFormat;
  initialFileName?: string;
  taskId?: string;
  singleLead?: Lead;
  // Optional custom title/subtitle
  dialogTitle?: string;
  dialogSubtitle?: string;
  onExportComplete?: (record: ExportRecord) => void;
}
