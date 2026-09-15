"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExportErrorProps {
  onRetry: () => void;
}

export function ExportError({ onRetry }: ExportErrorProps) {
  return (
    <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/60 text-rose-900 space-y-3">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-rose-100 text-rose-600 rounded-lg shrink-0 mt-0.5">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-rose-950">Export failed</h4>
          <p className="text-xs text-rose-800 mt-0.5 leading-relaxed">
            We couldn&apos;t create the export file. Please try again.
          </p>
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          type="button"
          size="sm"
          onClick={onRetry}
          className="bg-rose-600 hover:bg-rose-700 text-white text-xs gap-1.5 h-8"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Try Again</span>
        </Button>
      </div>
    </div>
  );
}
