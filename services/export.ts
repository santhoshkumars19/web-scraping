/**
 * services/export.ts
 *
 * REST API client service for Lead exports (CSV & Excel).
 * Connects the Next.js frontend to the FastAPI export endpoints:
 *   - /api/tasks/{task_id}/export/csv
 *   - /api/tasks/{task_id}/export/excel
 *   - /api/leads/export/csv
 *   - /api/leads/export/excel
 *   - /api/leads/{lead_id}/export/csv
 *   - /api/leads/{lead_id}/export/excel
 */

import { apiUrl, getStoredToken } from "@/lib/api";
import type { ExportFormat, ExportOptions } from "@/types/export";

export interface ExportQueryParams {
  taskId?: string;
  ids?: string[];
  fields?: string[];
  search?: string;
  category?: string;
  location?: string;
  verification?: string;
  hasPhone?: boolean;
  hasEmail?: boolean;
  hasWebsite?: boolean;
  hasWhatsapp?: boolean;
  hasContact?: boolean;
  hasSocial?: boolean;
  scrapedFrom?: string;
  scrapedTo?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

/**
 * Extract filename from Content-Disposition header or fallback.
 */
function extractFilename(
  contentDisposition: string | null,
  fallback: string
): string {
  if (!contentDisposition) return fallback;
  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  return match && match[1] ? match[1].trim() : fallback;
}

/**
 * Format bytes into human-readable string (KB, MB).
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 KB";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const val = bytes / Math.pow(k, i);
  return `${val.toFixed(val >= 10 || i === 0 ? 0 : 1)} ${sizes[i]}`;
}

/**
 * Trigger immediate browser download of a Blob.
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => window.URL.revokeObjectURL(url), 15000);
}

// ── Generic Export Fetcher ───────────────────────────────────────────────────

async function fetchExportBlob(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
  defaultFilename = "export"
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  const url = new URL(apiUrl(path));

  if (params) {
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "") {
        url.searchParams.set(key, String(val));
      }
    });
  }

  const headers: Record<string, string> = {
    Accept: "*/*",
  };
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url.toString(), {
    method: "GET",
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let errorDetail = "Export request failed.";
    try {
      const errJson = await res.json();
      errorDetail =
        errJson?.error?.message ||
        errJson?.detail?.message ||
        errJson?.detail ||
        `Export failed with status ${res.status}`;
    } catch {
      errorDetail = `Export failed with status ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }

  const blob = await res.blob();
  const filename = extractFilename(
    res.headers.get("Content-Disposition"),
    defaultFilename
  );
  const sizeFormatted = formatFileSize(blob.size);

  return { blob, filename, sizeFormatted };
}

// ── Task-Scoped Exports ──────────────────────────────────────────────────────

export async function exportTaskCsv(
  taskId: string,
  fields?: string[]
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return fetchExportBlob(
    `/api/tasks/${encodeURIComponent(taskId)}/export/csv`,
    { fields: fields?.join(",") },
    `leadscout-task-${taskId}.csv`
  );
}

export async function exportTaskExcel(
  taskId: string,
  fields?: string[]
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return fetchExportBlob(
    `/api/tasks/${encodeURIComponent(taskId)}/export/excel`,
    { fields: fields?.join(",") },
    `leadscout-task-${taskId}.xlsx`
  );
}

// ── Global / Filtered Leads Exports ──────────────────────────────────────────

export async function exportLeadsCsv(
  params: ExportQueryParams = {}
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return fetchExportBlob(
    "/api/leads/export/csv",
    {
      task_id: params.taskId,
      ids: params.ids?.join(","),
      fields: params.fields?.join(","),
      search: params.search,
      category: params.category,
      location: params.location,
      verification: params.verification,
      has_phone: params.hasPhone,
      has_email: params.hasEmail,
      has_website: params.hasWebsite,
      has_whatsapp: params.hasWhatsapp,
      has_contact: params.hasContact,
      has_social: params.hasSocial,
      scraped_from: params.scrapedFrom,
      scraped_to: params.scrapedTo,
      sort_by: params.sortBy,
      sort_order: params.sortOrder,
    },
    "leadscout-leads.csv"
  );
}

export async function exportLeadsExcel(
  params: ExportQueryParams = {}
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return fetchExportBlob(
    "/api/leads/export/excel",
    {
      task_id: params.taskId,
      ids: params.ids?.join(","),
      fields: params.fields?.join(","),
      search: params.search,
      category: params.category,
      location: params.location,
      verification: params.verification,
      has_phone: params.hasPhone,
      has_email: params.hasEmail,
      has_website: params.hasWebsite,
      has_whatsapp: params.hasWhatsapp,
      has_contact: params.hasContact,
      has_social: params.hasSocial,
      scraped_from: params.scrapedFrom,
      scraped_to: params.scrapedTo,
      sort_by: params.sortBy,
      sort_order: params.sortOrder,
    },
    "leadscout-leads.xlsx"
  );
}

// ── Selected Leads Exports ───────────────────────────────────────────────────

export async function exportSelectedCsv(
  leadIds: string[],
  fields?: string[]
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return exportLeadsCsv({ ids: leadIds, fields });
}

export async function exportSelectedExcel(
  leadIds: string[],
  fields?: string[]
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return exportLeadsExcel({ ids: leadIds, fields });
}

// ── Single Lead Exports ──────────────────────────────────────────────────────

export async function exportSingleLeadCsv(
  leadId: string,
  fields?: string[]
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return fetchExportBlob(
    `/api/leads/${encodeURIComponent(leadId)}/export/csv`,
    { fields: fields?.join(",") },
    `leadscout-lead-${leadId}.csv`
  );
}

export async function exportSingleLeadExcel(
  leadId: string,
  fields?: string[]
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  return fetchExportBlob(
    `/api/leads/${encodeURIComponent(leadId)}/export/excel`,
    { fields: fields?.join(",") },
    `leadscout-lead-${leadId}.xlsx`
  );
}

// ── Orchestrated Backend Export for ExportDialog ─────────────────────────────

export async function exportBackendFile(
  options: ExportOptions,
  onProgress?: (stage: "preparing" | "creating" | "downloading" | "complete") => void
): Promise<{ blob: Blob; filename: string; sizeFormatted: string }> {
  const { leads, format, fieldIds, fileName, sourceType, taskId } = options;

  onProgress?.("preparing");

  const fieldsParam = fieldIds && fieldIds.length > 0 ? (fieldIds as string[]) : undefined;

  onProgress?.("creating");

  let result: { blob: Blob; filename: string; sizeFormatted: string };

  // Dispatch based on context & sourceType
  if (sourceType === "SINGLE_LEAD" && leads && leads.length === 1 && leads[0].id) {
    result =
      format === "excel"
        ? await exportSingleLeadExcel(leads[0].id, fieldsParam)
        : await exportSingleLeadCsv(leads[0].id, fieldsParam);
  } else if (sourceType === "TASK" && taskId) {
    result =
      format === "excel"
        ? await exportTaskExcel(taskId, fieldsParam)
        : await exportTaskCsv(taskId, fieldsParam);
  } else if (sourceType === "SELECTED_LEADS" && leads && leads.length > 0) {
    const ids = leads.map((l) => l.id).filter(Boolean);
    result =
      format === "excel"
        ? await exportSelectedExcel(ids, fieldsParam)
        : await exportSelectedCsv(ids, fieldsParam);
  } else {
    // Global or Filtered leads
    result =
      format === "excel"
        ? await exportLeadsExcel({
            taskId,
            ids: leads && leads.length < 500 ? leads.map((l) => l.id).filter(Boolean) : undefined,
            fields: fieldsParam,
          })
        : await exportLeadsCsv({
            taskId,
            ids: leads && leads.length < 500 ? leads.map((l) => l.id).filter(Boolean) : undefined,
            fields: fieldsParam,
          });
  }

  // Use custom filename if user customized it
  let finalFilename = result.filename;
  if (fileName && fileName.trim()) {
    const ext = format === "excel" ? "xlsx" : "csv";
    const cleanCustom = fileName.trim().replace(/\.(csv|xlsx)$/i, "");
    if (!cleanCustom.toLowerCase().includes(result.filename.toLowerCase())) {
      finalFilename = `${cleanCustom}.${ext}`;
    }
  }

  onProgress?.("downloading");
  triggerBlobDownload(result.blob, finalFilename);

  onProgress?.("complete");

  return {
    blob: result.blob,
    filename: finalFilename,
    sizeFormatted: result.sizeFormatted,
  };
}
