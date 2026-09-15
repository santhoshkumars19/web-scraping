// ============================================================
// LeadScout — Excel (.xlsx) Export Utility
// ============================================================

import * as XLSX from "xlsx";
import type { Lead } from "@/types/lead";
import type { ExportFieldId } from "@/types/export";
import {
  sortFieldsToPredictableOrder,
  getFieldLabel,
  getLeadFieldValue,
  downloadBlob,
} from "./exportUtils";

/**
 * Generates and triggers browser download of an Excel (.xlsx) file for given leads
 */
export function exportToExcel(
  leads: Lead[],
  fieldIds: ExportFieldId[],
  fileNameWithoutExt: string
): { blob: Blob; fullFileName: string; sizeFormatted: string } {
  // 1. Order fields predictably
  const orderedFields = sortFieldsToPredictableOrder(fieldIds);

  // 2. Build headers
  const headers = orderedFields.map((f) => getFieldLabel(f));

  // 3. Build data rows as array of arrays (AOA)
  const rows: (string | number)[][] = [headers];

  leads.forEach((lead) => {
    const row = orderedFields.map((fieldId) => {
      const val = getLeadFieldValue(lead, fieldId);
      return val;
    });
    rows.push(row);
  });

  // 4. Create worksheet using aoa_to_sheet
  const ws = XLSX.utils.aoa_to_sheet(rows);

  // 5. Ensure phone numbers, pincodes, and numbers are treated explicitly as text
  // aoa_to_sheet cells: A1, B1, etc.
  const range = XLSX.utils.decode_range(ws["!ref"] || "A1");
  for (let R = range.s.r + 1; R <= range.e.r; ++R) {
    for (let C = range.s.c; C <= range.e.c; ++C) {
      const cellAddress = XLSX.utils.encode_cell({ r: R, c: C });
      const cell = ws[cellAddress];
      if (cell && cell.v !== undefined) {
        // Force string type 's' to preserve formatting, leading plus, and zeros
        cell.t = "s";
        cell.v = String(cell.v);
      }
    }
  }

  // 6. Set estimated column widths for high readability
  const colWidths = orderedFields.map((fieldId) => {
    switch (fieldId) {
      case "organizationName":
        return { wch: 32 };
      case "category":
        return { wch: 20 };
      case "website":
        return { wch: 28 };
      case "address":
        return { wch: 36 };
      case "city":
      case "state":
        return { wch: 16 };
      case "pincode":
        return { wch: 12 };
      case "phone":
      case "alternatePhone":
      case "whatsapp":
        return { wch: 18 };
      case "email":
        return { wch: 30 };
      case "contactPerson":
      case "designation":
        return { wch: 22 };
      case "facebook":
      case "instagram":
      case "linkedin":
      case "youtube":
      case "otherSocial":
        return { wch: 32 };
      case "sourceUrls":
        return { wch: 45 };
      case "verification":
        return { wch: 16 };
      case "scrapedDate":
      case "taskId":
        return { wch: 15 };
      default:
        return { wch: 18 };
    }
  });
  ws["!cols"] = colWidths;

  // 7. Create workbook and append sheet
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Discovered Leads");

  // 8. Generate array buffer and wrap into Blob
  const excelBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  const fullFileName = `${fileNameWithoutExt}.xlsx`;
  const blob = new Blob([excelBuffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });

  // Calculate formatted size
  const sizeBytes = blob.size;
  const sizeFormatted =
    sizeBytes > 1024 * 1024
      ? `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
      : `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;

  // 9. Trigger browser download
  downloadBlob(blob, fullFileName);

  return { blob, fullFileName, sizeFormatted };
}
