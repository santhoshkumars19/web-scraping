"use client";

import { Users, ShieldCheck, Mail, Phone, Globe } from "lucide-react";
import type { Lead } from "@/types/lead";

interface LeadSummaryCardsProps {
  leads: Lead[];
  totalUnfiltered: number;
  isFiltered: boolean;
}

export function LeadSummaryCards({
  leads,
  totalUnfiltered,
  isFiltered,
}: LeadSummaryCardsProps) {
  const total = leads.length;
  const verifiedCount = leads.filter(
    (l) => l.verification.status === "HIGH" || l.verification.status === "MEDIUM"
  ).length;
  const withEmailCount = leads.filter((l) => Boolean(l.email)).length;
  const withPhoneCount = leads.filter((l) => Boolean(l.phone)).length;
  const withWebsiteCount = leads.filter((l) => Boolean(l.website)).length;

  const cards = [
    {
      label: "Total Leads",
      value: total,
      subtext: isFiltered ? `Filtered from ${totalUnfiltered}` : "In current database",
      icon: Users,
      color: "text-primary bg-primary/10",
    },
    {
      label: "Verified",
      value: verifiedCount,
      subtext: `${total > 0 ? Math.round((verifiedCount / total) * 100) : 0}% coverage`,
      icon: ShieldCheck,
      color: "text-emerald-700 bg-emerald-50",
    },
    {
      label: "With Email",
      value: withEmailCount,
      subtext: `${total > 0 ? Math.round((withEmailCount / total) * 100) : 0}% has address`,
      icon: Mail,
      color: "text-amber-700 bg-amber-50",
    },
    {
      label: "With Phone",
      value: withPhoneCount,
      subtext: `${total > 0 ? Math.round((withPhoneCount / total) * 100) : 0}% reachable`,
      icon: Phone,
      color: "text-foreground bg-muted",
    },
    {
      label: "With Website",
      value: withWebsiteCount,
      subtext: `${total > 0 ? Math.round((withWebsiteCount / total) * 100) : 0}% online domain`,
      icon: Globe,
      color: "text-primary bg-primary/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 sm:gap-3">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={`rounded-xl sm:rounded-2xl border border-border bg-white p-3 sm:p-3.5 shadow-2xs hover:border-border/80 transition-colors ${
              idx === 4 ? "col-span-2 sm:col-span-1" : ""
            }`}
          >
            <div className="flex items-center justify-between gap-1.5">
              <span className="text-xs font-medium text-muted-foreground truncate">
                {card.label}
              </span>
              <div className={`p-1.5 rounded-md shrink-0 ${card.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-xl font-bold tracking-tight text-foreground">
                {card.value}
              </span>
              {card.label === "Total Leads" && isFiltered && (
                <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded font-medium">
                  Active
                </span>
              )}
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground truncate">
              {card.subtext}
            </p>
          </div>
        );
      })}
    </div>
  );
}
