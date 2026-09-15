"use client";

import { Check, X, Database } from "lucide-react";
import type { Lead } from "@/types/lead";

interface DataCoverageProps {
  lead: Lead;
}

export function DataCoverage({ lead }: DataCoverageProps) {
  const points = [
    { label: "Phone Number", available: Boolean(lead.phone) },
    { label: "Alternate Phone", available: Boolean(lead.alternatePhone) },
    { label: "Official Email", available: Boolean(lead.email) },
    { label: "Website Domain", available: Boolean(lead.website) },
    { label: "Physical Address", available: Boolean(lead.address) },
    { label: "WhatsApp Contact", available: Boolean(lead.whatsapp) },
    { label: "Contact Person", available: Boolean(lead.contactPerson) },
    {
      label: "Social Links",
      available: Boolean(lead.socialLinks && lead.socialLinks.length > 0),
    },
  ];

  const availableCount = points.filter((p) => p.available).length;
  const totalCount = points.length;
  const percentage = Math.round((availableCount / totalCount) * 100);

  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm space-y-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground uppercase tracking-wider">
          <Database className="h-4 w-4 text-primary" />
          <span>Data Coverage</span>
        </div>
        <span className="text-xs font-mono font-semibold text-primary">
          {availableCount} / {totalCount}
        </span>
      </div>

      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="divide-y divide-border/60 text-xs">
        {points.map((pt) => (
          <div
            key={pt.label}
            className="py-1.5 flex items-center justify-between"
          >
            <span
              className={
                pt.available
                  ? "text-foreground font-medium"
                  : "text-muted-foreground/60"
              }
            >
              {pt.label}
            </span>

            {pt.available ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600">
                <Check className="h-3 w-3 stroke-[3]" />
                <span>Available</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground/50">
                <X className="h-3 w-3" />
                <span>Missing</span>
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
