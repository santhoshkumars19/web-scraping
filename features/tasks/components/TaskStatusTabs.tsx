"use client";

import type { TaskHistoryStatus } from "@/types/task";

interface TaskStatusTabsProps {
  selectedStatus: TaskHistoryStatus | "ALL";
  onSelect: (status: TaskHistoryStatus | "ALL") => void;
  counts: {
    all: number;
    running: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
}

export function TaskStatusTabs({
  selectedStatus,
  onSelect,
  counts,
}: TaskStatusTabsProps) {
  const tabs: { id: TaskHistoryStatus | "ALL"; label: string; count: number }[] = [
    { id: "ALL", label: "All Tasks", count: counts.all },
    { id: "RUNNING", label: "Running", count: counts.running },
    { id: "COMPLETED", label: "Completed", count: counts.completed },
    { id: "FAILED", label: "Failed", count: counts.failed },
    { id: "CANCELLED", label: "Cancelled", count: counts.cancelled },
  ];

  return (
    <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg overflow-x-auto w-full sm:w-auto text-xs">
      {tabs.map((tab) => {
        const isSelected = selectedStatus === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onSelect(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium whitespace-nowrap transition-all ${
              isSelected
                ? "bg-white text-foreground shadow-2xs font-semibold"
                : "text-muted-foreground hover:text-foreground hover:bg-white/50"
            }`}
          >
            <span>{tab.label}</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                isSelected
                  ? "bg-primary/10 text-primary font-bold"
                  : "bg-slate-200/80 text-muted-foreground"
              }`}
            >
              {tab.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
