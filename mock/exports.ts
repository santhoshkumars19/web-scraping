// ============================================================
// LeadScout — Mock Export History & Storage Utilities
// ============================================================

import type { ExportRecord, ExportFormat, ExportSourceType, ExportStatus } from "@/types/export";

const EXPORT_STORAGE_KEY = "leadscout_export_history";

/**
 * In-memory session cache for newly generated file Blobs,
 * allowing instant re-downloading during the active browser session.
 */
export const SESSION_EXPORT_BLOBS = new Map<
  string,
  { blob: Blob; fileName: string; format: ExportFormat }
>();

export const INITIAL_MOCK_EXPORTS: ExportRecord[] = [
  {
    id: "exp-001",
    fileName: "leadscout-leads-2026-09-11.xlsx",
    format: "excel",
    recordCount: 61,
    createdAt: "Sep 11, 2026, 09:15 AM",
    status: "COMPLETED",
    sourceType: "ALL_LEADS",
    fileSize: "28 KB",
  },
  {
    id: "exp-002",
    fileName: "leadscout-schools-puducherry.csv",
    format: "csv",
    recordCount: 100,
    createdAt: "Sep 10, 2026, 04:30 PM",
    status: "COMPLETED",
    taskId: "TASK-000124",
    sourceType: "TASK",
    fileSize: "34 KB",
  },
  {
    id: "exp-003",
    fileName: "leadscout-selected-coimbatore.xlsx",
    format: "excel",
    recordCount: 14,
    createdAt: "Sep 09, 2026, 11:20 AM",
    status: "COMPLETED",
    sourceType: "SELECTED_LEADS",
    fileSize: "16 KB",
  },
  {
    id: "exp-004",
    fileName: "leadscout-pondicherry-public-school.xlsx",
    format: "excel",
    recordCount: 1,
    createdAt: "Sep 08, 2026, 02:45 PM",
    status: "COMPLETED",
    sourceType: "SINGLE_LEAD",
    fileSize: "12 KB",
  },
  {
    id: "exp-005",
    fileName: "leadscout-chennai-filtered.csv",
    format: "csv",
    recordCount: 0,
    createdAt: "Sep 07, 2026, 06:10 PM",
    status: "FAILED",
    sourceType: "FILTERED_LEADS",
    fileSize: "0 KB",
  },
];

/**
 * Load export records from localStorage or fallback to defaults
 */
export function loadExportHistory(): ExportRecord[] {
  if (typeof window === "undefined") return INITIAL_MOCK_EXPORTS;

  try {
    const raw = localStorage.getItem(EXPORT_STORAGE_KEY);
    if (raw) {
      const parsed: ExportRecord[] = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {}

  return INITIAL_MOCK_EXPORTS;
}

/**
 * Save export records to localStorage
 */
export function saveExportHistory(records: ExportRecord[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(EXPORT_STORAGE_KEY, JSON.stringify(records));
  } catch {}
}

/**
 * Add a newly generated export to history
 */
export function addExportRecord(
  params: Omit<ExportRecord, "id" | "createdAt"> & { blob?: Blob }
): ExportRecord {
  const newRecord: ExportRecord = {
    id: `exp-${Date.now().toString(36)}`,
    fileName: params.fileName,
    format: params.format,
    recordCount: params.recordCount,
    createdAt: new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
    status: params.status,
    taskId: params.taskId,
    sourceType: params.sourceType,
    fileSize: params.fileSize || "18 KB",
  };

  if (params.blob) {
    SESSION_EXPORT_BLOBS.set(newRecord.id, {
      blob: params.blob,
      fileName: params.fileName,
      format: params.format,
    });
  }

  const existing = loadExportHistory();
  const updated = [newRecord, ...existing];
  saveExportHistory(updated);

  return newRecord;
}

/**
 * Delete a specific export record from history
 */
export function deleteExportRecord(id: string): ExportRecord[] {
  SESSION_EXPORT_BLOBS.delete(id);
  const existing = loadExportHistory();
  const updated = existing.filter((r) => r.id !== id);
  saveExportHistory(updated);
  return updated;
}

/**
 * Clear all export history
 */
export function clearAllExportHistory(): void {
  SESSION_EXPORT_BLOBS.clear();
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(EXPORT_STORAGE_KEY, JSON.stringify([]));
    } catch {}
  }
}
