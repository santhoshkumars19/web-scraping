"use client";

import { TrendingUp, TrendingDown, Users, Globe, ShieldCheck, ListTodo } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MetricData } from "@/mock/dashboard";

const iconMap: Record<string, React.ElementType> = {
  total_leads: Users,
  websites_discovered: Globe,
  verified_leads: ShieldCheck,
  scraping_tasks: ListTodo,
};

interface MetricCardProps {
  metric: MetricData;
}

export function MetricCard({ metric }: MetricCardProps) {
  const Icon = iconMap[metric.id] ?? Users;
  const isPositive = metric.changePositive;

  return (
    <div className="rounded-2xl border border-border bg-white p-5 shadow-sm transition-all hover:shadow-md">
      {/* Top row: label + icon */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-semibold text-[#5C5A53] leading-none">
          {metric.label}
        </p>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#BE0B31]/10">
          <Icon className="h-4 w-4 text-[#BE0B31]" />
        </div>
      </div>

      {/* Value */}
      <p className="mt-3 text-2xl sm:text-3xl font-extrabold tracking-[-0.03em] text-[#0E0E0E]">
        {metric.value}
      </p>

      {/* Trend */}
      <div className="mt-2 flex items-center gap-1.5">
        <span
          className={cn(
            "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold",
            isPositive
              ? "bg-emerald-50 text-emerald-700"
              : "bg-rose-50 text-rose-700"
          )}
        >
          {isPositive ? (
            <TrendingUp className="h-3 w-3" />
          ) : (
            <TrendingDown className="h-3 w-3" />
          )}
          {metric.change}
        </span>
        <span className="text-xs text-muted-foreground">{metric.changeLabel}</span>
      </div>
    </div>
  );
}
