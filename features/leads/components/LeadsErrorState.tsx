"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LeadsErrorStateProps {
  onRetry: () => void;
}

export function LeadsErrorState({ onRetry }: LeadsErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-rose-200 bg-rose-50/30">
      <div className="p-3 bg-rose-100 rounded-full text-rose-600 mb-3">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <h3 className="text-base font-bold text-rose-950">Unable to load leads</h3>
      <p className="text-xs text-rose-800/80 mt-1 max-w-sm">
        Something went wrong while loading your leads. Please try again.
      </p>
      <Button
        variant="outline"
        size="sm"
        onClick={onRetry}
        className="mt-4 gap-1.5 text-xs bg-white hover:bg-slate-50 border-rose-200"
      >
        <RefreshCw className="h-3.5 w-3.5" />
        <span>Retry</span>
      </Button>
    </div>
  );
}
