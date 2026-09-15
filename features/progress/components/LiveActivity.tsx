"use client";

import { Activity, CheckCircle2, Info, AlertTriangle, XCircle } from "lucide-react";
import type { ActivityEntry } from "@/types/progress";

interface LiveActivityProps {
  activityLog: ActivityEntry[];
}

export function LiveActivity({ activityLog }: LiveActivityProps) {
  const getIcon = (type: ActivityEntry["type"]) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />;
      case "warning":
        return <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />;
      case "error":
        return <XCircle className="h-3.5 w-3.5 text-rose-600" />;
      default:
        return <Info className="h-3.5 w-3.5 text-blue-600" />;
    }
  };

  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Live Activity</h2>
        </div>
        <span className="text-[11px] text-muted-foreground font-mono">
          {activityLog.length} events logged
        </span>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[380px] pr-2 space-y-3">
        {activityLog.map((entry, index) => (
          <div
            key={entry.id || index}
            className="flex items-start gap-3 text-xs group"
          >
            <span className="font-mono text-muted-foreground/70 shrink-0 text-[11px] pt-0.5">
              {entry.timestamp}
            </span>
            <div className="mt-0.5 shrink-0">{getIcon(entry.type)}</div>
            <div className="flex-1 min-w-0">
              <p className="text-foreground leading-snug">{entry.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
