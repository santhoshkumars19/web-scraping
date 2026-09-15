"use client";

import { FileText, FileSpreadsheet } from "lucide-react";
import type { ExportFormat } from "@/types/export";

interface ExportFormatSelectorProps {
  format: ExportFormat;
  onFormatChange: (format: ExportFormat) => void;
}

export function ExportFormatSelector({
  format,
  onFormatChange,
}: ExportFormatSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-xs font-semibold text-foreground uppercase tracking-wider block">
        File Format
      </label>

      <div className="grid grid-cols-2 gap-3">
        {/* CSV Option */}
        <button
          type="button"
          onClick={() => onFormatChange("csv")}
          className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
            format === "csv"
              ? "border-primary bg-primary/5 text-foreground ring-1 ring-primary/20"
              : "border-border text-muted-foreground hover:border-border/80 hover:bg-slate-50/50"
          }`}
        >
          <div
            className={`p-2 rounded-md ${
              format === "csv" ? "bg-primary text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <span>CSV Spreadsheet</span>
              <span className="text-[10px] font-mono text-muted-foreground bg-slate-100 px-1 py-0.2 rounded">
                .csv
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5 leading-snug">
              Standard comma-delimited text with UTF-8 BOM. Universal support.
            </p>
          </div>
        </button>

        {/* Excel Option */}
        <button
          type="button"
          onClick={() => onFormatChange("excel")}
          className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
            format === "excel"
              ? "border-primary bg-primary/5 text-foreground ring-1 ring-primary/20"
              : "border-border text-muted-foreground hover:border-border/80 hover:bg-slate-50/50"
          }`}
        >
          <div
            className={`p-2 rounded-md ${
              format === "excel" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            <FileSpreadsheet className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <span>Excel Workbook</span>
              <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-1 py-0.2 rounded border border-emerald-200">
                .xlsx
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5 leading-snug">
              Native Microsoft Excel worksheet with preserved text formatting.
            </p>
          </div>
        </button>
      </div>
    </div>
  );
}
