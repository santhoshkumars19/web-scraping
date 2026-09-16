"use client";

import { ListFilter, Play, CheckCircle2, AlertOctagon, XCircle } from "lucide-react";
import type { TaskItem } from "@/types/task";

interface TaskSummaryCardsProps {
  tasks: TaskItem[];
  totalUnfiltered: number;
  isFiltered: boolean;
}

export function TaskSummaryCards({
  tasks,
  totalUnfiltered,
  isFiltered,
}: TaskSummaryCardsProps) {
  const total = tasks.length;
  const runningCount = tasks.filter((t) => t.status === "RUNNING").length;
  const completedCount = tasks.filter((t) => t.status === "COMPLETED").length;
  const failedCount = tasks.filter((t) => t.status === "FAILED").length;
  const cancelledCount = tasks.filter((t) => t.status === "CANCELLED").length;

  const cards = [
    {
      label: "Total Tasks",
      value: total,
      subtext: isFiltered ? `Filtered from ${totalUnfiltered}` : "Recorded tasks",
      icon: ListFilter,
      color: "text-primary bg-primary/10",
    },
    {
      label: "Running",
      value: runningCount,
      subtext: "Active extraction",
      icon: Play,
      color: "text-primary bg-primary/10",
    },
    {
      label: "Completed",
      value: completedCount,
      subtext: `${total > 0 ? Math.round((completedCount / total) * 100) : 0}% success rate`,
      icon: CheckCircle2,
      color: "text-emerald-700 bg-emerald-50",
    },
    {
      label: "Failed",
      value: failedCount,
      subtext: failedCount > 0 ? "Requires review" : "Zero errors",
      icon: AlertOctagon,
      color: failedCount > 0 ? "text-primary bg-primary/10" : "text-muted-foreground bg-muted",
    },
    {
      label: "Cancelled",
      value: cancelledCount,
      subtext: "Stopped by user",
      icon: XCircle,
      color: "text-muted-foreground bg-muted",
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
              <span className="text-xl font-bold tracking-tight text-foreground font-mono">
                {card.value}
              </span>
              {card.label === "Total Tasks" && isFiltered && (
                <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded font-medium">
                  Active Filter
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
