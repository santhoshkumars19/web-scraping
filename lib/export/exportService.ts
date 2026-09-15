// ============================================================
// LeadScout — Export Service (Orchestrator)
// ============================================================

import type { ExportOptions, ExportRecord } from "@/types/export";
import { exportToCsv } from "./csv";
import { exportToExcel } from "./excel";
import { sanitizeFileName } from "./exportUtils";
import { addExportRecord } from "@/mock/exports";
import { toast } from "sonner";

export interface ExportProgressCallback {
  (stage: "preparing" | "creating" | "downloading" | "complete"): void;
}

/**
 * Execute client-side export workflow:
 * 1. Sanitizes filename
 * 2. Simulates brief async generation phases
 * 3. Builds and triggers download
 * 4. Logs to export history
 * 5. Displays confirmation toast
 */
export async function runExport(
  options: ExportOptions,
  onProgress?: ExportProgressCallback
): Promise<{ success: boolean; record: ExportRecord; error?: string }> {
  const { leads, format, fieldIds, fileName, sourceType, taskId } = options;

  if (!leads || leads.length === 0) {
    throw new Error("No leads available to export.");
  }

  if (!fieldIds || fieldIds.length === 0) {
    throw new Error("Select at least one field.");
  }

  const cleanFileName = sanitizeFileName(fileName);

  try {
    // Stage 1: Preparing
    onProgress?.("preparing");
    await new Promise((resolve) => setTimeout(resolve, 250));

    // Stage 2: Creating
    onProgress?.("creating");
    await new Promise((resolve) => setTimeout(resolve, 250));

    let result: { blob: Blob; fullFileName: string; sizeFormatted: string };

    try {
      // 1. Primary: Use real FastAPI backend export API
      const { exportBackendFile } = await import("@/services/export");
      const backendRes = await exportBackendFile(options, onProgress);
      result = {
        blob: backendRes.blob,
        fullFileName: backendRes.filename,
        sizeFormatted: backendRes.sizeFormatted,
      };
    } catch (apiErr) {
      console.warn("Backend export API call failed; using client-side fallback:", apiErr);
      // 2. Fallback: Client-side export generation
      if (format === "excel") {
        result = exportToExcel(leads, fieldIds, cleanFileName);
      } else {
        result = exportToCsv(leads, fieldIds, cleanFileName);
      }
      onProgress?.("downloading");
    }

    // Stage 4: Add to Export History
    const record = addExportRecord({
      fileName: result.fullFileName,
      format,
      recordCount: leads.length,
      status: "COMPLETED",
      taskId,
      sourceType,
      fileSize: result.sizeFormatted,
      blob: result.blob,
    });

    onProgress?.("complete");

    // Success Toast
    const formatName = format === "excel" ? "Excel" : "CSV";
    toast.success("Export completed.", {
      description: `${leads.length} ${
        leads.length === 1 ? "lead" : "leads"
      } exported as ${formatName}.`,
    });

    return {
      success: true,
      record,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Export failed";

    // Register failure record in history if an unexpected failure occurred
    addExportRecord({
      fileName: `${cleanFileName}.${format === "excel" ? "xlsx" : "csv"}`,
      format,
      recordCount: leads.length,
      status: "FAILED",
      taskId,
      sourceType,
      fileSize: "0 KB",
    });

    return {
      success: false,
      record: {
        id: `failed-${Date.now()}`,
        fileName: `${cleanFileName}.${format === "excel" ? "xlsx" : "csv"}`,
        format,
        recordCount: 0,
        createdAt: new Date().toLocaleDateString(),
        status: "FAILED",
        sourceType,
      },
      error: message,
    };
  }
}
