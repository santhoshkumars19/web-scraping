"use client";

import { Input } from "@/components/ui/input";
import type { ExportFormat } from "@/types/export";
import { sanitizeFileName } from "@/lib/export/exportUtils";

interface ExportFileNameProps {
  fileName: string;
  onFileNameChange: (name: string) => void;
  format: ExportFormat;
}

export function ExportFileName({
  fileName,
  onFileNameChange,
  format,
}: ExportFileNameProps) {
  const extension = format === "excel" ? ".xlsx" : ".csv";
  const isValid = fileName.trim().length > 0;
  const sanitizedPreview = `${sanitizeFileName(fileName)}${extension}`;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label
          htmlFor="export-file-name"
          className="text-xs font-semibold text-foreground uppercase tracking-wider"
        >
          File Name
        </label>
        <span className="text-[11px] font-mono text-muted-foreground truncate max-w-[200px]">
          Preview: {sanitizedPreview}
        </span>
      </div>

      <div className="flex items-center rounded-lg border border-input bg-white shadow-2xs focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary overflow-hidden">
        <Input
          id="export-file-name"
          type="text"
          value={fileName}
          onChange={(e) => onFileNameChange(e.target.value)}
          placeholder="leadscout-leads"
          className="border-0 shadow-none focus-visible:ring-0 text-xs h-9"
        />
        <div className="px-3 py-1 bg-slate-100 border-l border-border text-xs font-mono font-medium text-slate-700 select-none">
          {extension}
        </div>
      </div>

      {!isValid && (
        <p className="text-[11px] text-rose-600 font-medium">
          File name cannot be empty.
        </p>
      )}
    </div>
  );
}
