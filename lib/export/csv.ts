// ============================================================
// LeadScout — CSV Export Utility
// ============================================================

import type { Lead } from "@/types/lead";
import type { ExportFieldId } from "@/types/export";
import {
  sortFieldsToPredictableOrder,
  getFieldLabel,
  getLeadFieldValue,
  downloadBlob,
} from "./exportUtils";

/**
 * Escapes a single CSV cell value according to RFC 4180
 */
function escapeCsvValue(val: string): string {
  if (val === null || val === undefined) return "";
  const str = String(val);

  // If cell contains commas, quotes, carriage returns or newlines, wrap in quotes and escape quotes
  if (/[",\r\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }

  // Preserve phone numbers or identifiers with leading plus or hyphen as text
  // Quoting them preserves formatting in spreadsheet readers without triggering formulas
  if (/^[+\-=@]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }

  return str;
}

/**
 * Generates and triggers browser download of a CSV file for given leads
 */
export function exportToCsv(
  leads: Lead[],
  fieldIds: ExportFieldId[],
  fileNameWithoutExt: string
): { blob: Blob; fullFileName: string; sizeFormatted: string } {
  // 1. Order fields predictably
  const orderedFields = sortFieldsToPredictableOrder(fieldIds);

  // 2. Build header row
  const headerRow = orderedFields.map((f) => escapeCsvValue(getFieldLabel(f))).join(",");

  // 3. Build data rows
  const dataRows = leads.map((lead) => {
    return orderedFields
      .map((fieldId) => {
        const value = getLeadFieldValue(lead, fieldId);
        return escapeCsvValue(value);
      })
      .join(",");
  });

  // 4. Combine with UTF-8 BOM (\uFEFF) for Excel Unicode compatibility
  const csvContent = "\uFEFF" + [headerRow, ...dataRows].join("\r\n");

  const fullFileName = `${fileNameWithoutExt}.csv`;
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });

  // Calculate human-readable size
  const sizeBytes = blob.size;
  const sizeFormatted =
    sizeBytes > 1024 * 1024
      ? `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
      : `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;

  // 5. Trigger download in browser
  downloadBlob(blob, fullFileName);

  return { blob, fullFileName, sizeFormatted };
}
