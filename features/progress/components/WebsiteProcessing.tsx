"use client";

import { Globe, ShieldCheck, CheckCircle2, Clock, AlertTriangle, XCircle, Loader2 } from "lucide-react";
import type { WebsiteEntry, WebsiteStatus } from "@/types/progress";

interface WebsiteProcessingProps {
  websites: WebsiteEntry[];
  successfulCount: number;
  failedCount: number;
  blockedCount: number;
  timeoutCount: number;
}

export function WebsiteProcessing({
  websites,
  successfulCount,
  failedCount,
  blockedCount,
  timeoutCount,
}: WebsiteProcessingProps) {
  const getStatusBadge = (status: WebsiteStatus) => {
    switch (status) {
      case "SUCCESS":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700">
            <CheckCircle2 className="h-3 w-3" />
            Success
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary">
            <Loader2 className="h-3 w-3 animate-spin" />
            Crawling
          </span>
        );
      case "TIMEOUT":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700">
            <Clock className="h-3 w-3" />
            Timeout
          </span>
        );
      case "BLOCKED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-50 text-purple-700">
            <AlertTriangle className="h-3 w-3" />
            Blocked
          </span>
        );
      case "FAILED":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-50 text-rose-700">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-white shadow-sm flex flex-col h-full">
      {/* Header & Status Summary */}
      <div className="p-5 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold tracking-tight text-foreground">Website Processing</h2>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {websites.length} domains listed
          </span>
        </div>

        {/* Counter Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="bg-emerald-50/70 border border-emerald-100 rounded-lg p-2 flex items-center justify-between">
            <span className="text-xs text-emerald-800 font-medium">Successful</span>
            <span className="text-xs font-bold text-emerald-800">{successfulCount}</span>
          </div>
          <div className="bg-amber-50/70 border border-amber-100 rounded-lg p-2 flex items-center justify-between">
            <span className="text-xs text-amber-800 font-medium">Timeout</span>
            <span className="text-xs font-bold text-amber-800">{timeoutCount}</span>
          </div>
          <div className="bg-purple-50/70 border border-purple-100 rounded-lg p-2 flex items-center justify-between">
            <span className="text-xs text-purple-800 font-medium">Blocked</span>
            <span className="text-xs font-bold text-purple-800">{blockedCount}</span>
          </div>
          <div className="bg-rose-50/70 border border-rose-100 rounded-lg p-2 flex items-center justify-between">
            <span className="text-xs text-rose-800 font-medium">Failed</span>
            <span className="text-xs font-bold text-rose-800">{failedCount}</span>
          </div>
        </div>
      </div>

      {/* Website Table */}
      <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-50/90 backdrop-blur-xs border-b border-border text-muted-foreground font-medium z-10">
            <tr>
              <th className="py-2.5 px-4">Organization</th>
              <th className="py-2.5 px-3">Website</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-4 text-right">Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {websites.map((site, index) => (
              <tr key={`${site.domain}-${index}`} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-2 px-4 font-medium text-foreground max-w-[180px] truncate" title={site.organization}>
                  {site.organization}
                </td>
                <td className="py-2 px-3 text-muted-foreground font-mono text-[11px] max-w-[180px] truncate" title={site.domain}>
                  {site.domain}
                </td>
                <td className="py-2 px-3 whitespace-nowrap">
                  {getStatusBadge(site.status)}
                </td>
                <td className="py-2 px-4 text-right text-muted-foreground text-[11px] truncate max-w-[160px]" title={site.reason || "—"}>
                  {site.reason || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer Note */}
      <div className="p-3 bg-slate-50/60 border-t border-border rounded-b-xl flex items-center gap-2 text-[11px] text-muted-foreground">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
        <span>Restricted access policies and robots.txt are respected automatically.</span>
      </div>
    </div>
  );
}
