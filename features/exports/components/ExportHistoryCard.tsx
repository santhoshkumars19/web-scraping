"use client";

import {
  FileText,
  FileSpreadsheet,
  Download,
  Trash2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ExportRecord } from "@/types/export";

interface ExportHistoryCardProps {
  record: ExportRecord;
  onDownload: (record: ExportRecord) => void;
  onDeleteRequest: (record: ExportRecord) => void;
}

export function ExportHistoryCard({
  record,
  onDownload,
  onDeleteRequest,
}: ExportHistoryCardProps) {
  const isExcel = record.format === "excel";
  const isSuccess = record.status === "COMPLETED";

  return (
    <div className="rounded-2xl border border-border/80 bg-white p-3.5 space-y-3 shadow-2xs">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <div
            className={`p-2 rounded-xl shrink-0 mt-0.5 ${
              isExcel
                ? "bg-emerald-50 text-emerald-700"
                : "bg-primary/10 text-primary"
            }`}
          >
            {isExcel ? (
              <FileSpreadsheet className="h-4 w-4" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
          </div>
          <div className="min-w-0">
            <h4
              className="text-xs font-semibold text-foreground truncate"
              title={record.fileName}
            >
              {record.fileName}
            </h4>
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
              <span>{record.createdAt}</span>
              <span>•</span>
              <span className="font-mono">{record.fileSize || "18 KB"}</span>
            </div>
          </div>
        </div>

        {/* Status Badge */}
        {isSuccess ? (
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 shrink-0">
            <CheckCircle2 className="h-2.5 w-2.5" />
            <span>Completed</span>
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200 shrink-0">
            <XCircle className="h-2.5 w-2.5" />
            <span>Failed</span>
          </span>
        )}
      </div>

      {/* Meta Bar */}
      <div className="flex items-center justify-between text-xs py-2 px-3 rounded-lg bg-slate-50 border border-border/50">
        <div>
          <span className="text-muted-foreground text-[11px]">Format: </span>
          <span className="font-semibold uppercase text-[10px] font-mono">
            {record.format}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground text-[11px]">Records: </span>
          <span className="font-bold font-mono text-foreground">
            {record.recordCount}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-1 border-t border-border/60">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!isSuccess}
          onClick={() => onDownload(record)}
          className="h-8 text-xs gap-1.5 flex-1 mr-2"
        >
          <Download className="h-3.5 w-3.5" />
          <span>Download File</span>
        </Button>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onDeleteRequest(record)}
          className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive hover:bg-rose-50"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span className="sr-only">Delete</span>
        </Button>
      </div>
    </div>
  );
}
