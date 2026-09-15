"use client";

import { Activity, Search, Globe, Compass, Phone, Mail, CheckCircle2 } from "lucide-react";
import type { Lead } from "@/types/lead";

interface LeadActivityProps {
  lead: Lead;
}

export function LeadActivity({ lead }: LeadActivityProps) {
  const events = [
    {
      label: "Organization discovered in local business directory",
      icon: Search,
      time: `${lead.scrapedDate} • 10:42:08 AM`,
    },
    {
      label: `Official website domain identified (${lead.website ? "found" : "fallback"})`,
      icon: Globe,
      time: `${lead.scrapedDate} • 10:42:15 AM`,
    },
    {
      label: "Public contact and admission pages visited",
      icon: Compass,
      time: `${lead.scrapedDate} • 10:42:35 AM`,
    },
    ...(lead.phone
      ? [
          {
            label: `Phone number ${lead.phone} extracted and standardized`,
            icon: Phone,
            time: `${lead.scrapedDate} • 10:42:51 AM`,
          },
        ]
      : []),
    ...(lead.email
      ? [
          {
            label: `Official email ${lead.email} discovered on contact page`,
            icon: Mail,
            time: `${lead.scrapedDate} • 10:43:02 AM`,
          },
        ]
      : []),
    {
      label: `Record normalized, deduplicated, and saved under task ${lead.taskId}`,
      icon: CheckCircle2,
      time: `${lead.scrapedDate} • 10:43:18 AM`,
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-white p-5 sm:p-6 shadow-sm">
      <div className="flex items-center gap-2 border-b border-border pb-3 mb-4">
        <Activity className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">Lead Activity History</h2>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {events.map((event, idx) => {
          const Icon = event.icon;
          return (
            <div key={idx} className="relative group">
              <div className="absolute -left-6 top-0.5 h-4 w-4 rounded-full bg-white border-2 border-primary flex items-center justify-center">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              </div>

              <div className="text-xs">
                <p className="font-medium text-foreground">{event.label}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">
                  {event.time}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
