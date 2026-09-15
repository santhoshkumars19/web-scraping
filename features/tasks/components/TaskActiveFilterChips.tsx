"use client";

import { X } from "lucide-react";
import type { TaskFilterState, TaskHistoryStatus } from "@/types/task";

interface TaskActiveFilterChipsProps {
  filters: TaskFilterState;
  onFilterChange: (filters: TaskFilterState) => void;
  onReset: () => void;
}

export function TaskActiveFilterChips({
  filters,
  onFilterChange,
  onReset,
}: TaskActiveFilterChipsProps) {
  const chips: { label: string; onRemove: () => void }[] = [];

  if (filters.search) {
    chips.push({
      label: `Search: "${filters.search}"`,
      onRemove: () => onFilterChange({ ...filters, search: "" }),
    });
  }

  filters.status.forEach((st: TaskHistoryStatus) => {
    chips.push({
      label: `Status: ${st}`,
      onRemove: () =>
        onFilterChange({
          ...filters,
          status: filters.status.filter((s) => s !== st),
        }),
    });
  });

  filters.locations.forEach((loc) => {
    chips.push({
      label: `Location: ${loc}`,
      onRemove: () =>
        onFilterChange({
          ...filters,
          locations: filters.locations.filter((l) => l !== loc),
        }),
    });
  });

  if (filters.hasResults !== "all") {
    chips.push({
      label: filters.hasResults === "has_results" ? "Has Results" : "No Results",
      onRemove: () => onFilterChange({ ...filters, hasResults: "all" }),
    });
  }

  if (filters.dateRange !== "all") {
    const labels: Record<string, string> = {
      today: "Today",
      "7d": "Last 7 days",
      "30d": "Last 30 days",
      "90d": "Last 90 days",
      custom: "Custom Date",
    };
    chips.push({
      label: `Date: ${labels[filters.dateRange] || filters.dateRange}`,
      onRemove: () => onFilterChange({ ...filters, dateRange: "all" }),
    });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 pt-1 pb-2">
      <span className="text-xs text-muted-foreground mr-1">Active filters:</span>
      {chips.map((chip, idx) => (
        <span
          key={idx}
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/8 text-primary border border-primary/20"
        >
          <span>{chip.label}</span>
          <button
            type="button"
            onClick={chip.onRemove}
            className="hover:text-primary/70 transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}

      <button
        type="button"
        onClick={onReset}
        className="text-xs text-muted-foreground hover:text-foreground underline ml-2"
      >
        Clear all
      </button>
    </div>
  );
}
