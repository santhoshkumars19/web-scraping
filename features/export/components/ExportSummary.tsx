"use client";

import type { ExportFormat } from "@/types/export";
import { sanitizeFileName } from "@/lib/export/exportUtils";

interface ExportSummaryProps {
  recordCount: number;
  format: ExportFormat;
  fieldCount: number;
  fileName: string;
}

export function ExportSummary({
  recordCount,
  format,
  fieldCount,
  fileName,
}: ExportSummaryProps) {
  const extension = format === "excel" ? ".xlsx" : ".csv";
  const cleanName = `${sanitizeFileName(fileName)}${extension}`;

  return (
    <div className="rounded-xl border border-border/80 bg-slate-50/60 p-3.5 space-y-2.5">
      <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Export Summary
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2 rounded-lg bg-white border border-border/60">
          <div className="text-[10px] text-muted-foreground uppercase font-medium">
            Records
          </div>
          <div className="text-xs font-bold font-mono text-foreground mt-0.5">
            {recordCount} {recordCount === 1 ? "lead" : "leads"}
          </div>
        </div>

        <div className="p-2 rounded-lg bg-white border border-border/60">
          <div className="text-[10px] text-muted-foreground uppercase font-medium">
            Format
          </div>
          <div className="text-xs font-bold text-foreground mt-0.5">
            {format === "excel" ? "Excel (.xlsx)" : "CSV (.csv)"}
          </div>
        </div>

        <div className="p-2 rounded-lg bg-white border border-border/60">
          <div className="text-[10px] text-muted-foreground uppercase font-medium">
            Fields
          </div>
          <div className="text-xs font-bold font-mono text-foreground mt-0.5">
            {fieldCount}
          </div>
        </div>

        <div className="p-2 rounded-lg bg-white border border-border/60">
          <div className="text-[10px] text-muted-foreground uppercase font-medium">
            File Name
          </div>
          <div className="text-[11px] font-mono font-medium text-foreground truncate mt-0.5" title={cleanName}>
            {cleanName}
          </div>
        </div>
      </div>
    </div>
  );
}
