"use client";

import { useState } from "react";
import { Filter, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { TaskFilterState, TaskHistoryStatus } from "@/types/task";

interface TaskFiltersProps {
  filters: TaskFilterState;
  onFilterChange: (filters: TaskFilterState) => void;
  onReset: () => void;
  activeCount: number;
}

const STATUS_OPTIONS: { id: TaskHistoryStatus; label: string }[] = [
  { id: "RUNNING", label: "Running" },
  { id: "COMPLETED", label: "Completed" },
  { id: "FAILED", label: "Failed" },
  { id: "CANCELLED", label: "Cancelled" },
];

const LOCATION_OPTIONS = [
  "Puducherry",
  "Chennai",
  "Coimbatore",
  "Madurai",
  "Bangalore",
];

const DATE_OPTIONS: { id: TaskFilterState["dateRange"]; label: string }[] = [
  { id: "all", label: "All Time" },
  { id: "today", label: "Today" },
  { id: "7d", label: "Last 7 days" },
  { id: "30d", label: "Last 30 days" },
  { id: "90d", label: "Last 90 days" },
  { id: "custom", label: "Custom Date" },
];

export function TaskFilters({
  filters,
  onFilterChange,
  onReset,
  activeCount,
}: TaskFiltersProps) {
  const [open, setOpen] = useState(false);

  const toggleStatus = (st: TaskHistoryStatus) => {
    const next = filters.status.includes(st)
      ? filters.status.filter((s) => s !== st)
      : [...filters.status, st];
    onFilterChange({ ...filters, status: next });
  };

  const toggleLocation = (loc: string) => {
    const next = filters.locations.includes(loc)
      ? filters.locations.filter((l) => l !== loc)
      : [...filters.locations, loc];
    onFilterChange({ ...filters, locations: next });
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="default"
          className="h-10 gap-2 text-xs font-medium relative bg-white border-border"
        >
          <Filter className="h-3.5 w-3.5 text-muted-foreground" />
          <span>Filters</span>
          {activeCount > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white">
              {activeCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-80 p-0 sm:w-96 shadow-lg border-border" align="start">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-slate-50/70">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold text-foreground">Filter Tasks</span>
          </div>
          {activeCount > 0 && (
            <button
              onClick={onReset}
              className="flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <RotateCcw className="h-3 w-3" />
              Reset all
            </button>
          )}
        </div>

        {/* Scrollable Filter List */}
        <div className="max-h-[420px] overflow-y-auto p-4 space-y-5 text-xs">
          {/* Status */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Task Status
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {STATUS_OPTIONS.map((st) => (
                <label
                  key={st.id}
                  className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground"
                >
                  <Checkbox
                    checked={filters.status.includes(st.id)}
                    onCheckedChange={() => toggleStatus(st.id)}
                  />
                  <span>{st.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Location */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Search Location
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {LOCATION_OPTIONS.map((loc) => (
                <label
                  key={loc}
                  className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground"
                >
                  <Checkbox
                    checked={filters.locations.includes(loc)}
                    onCheckedChange={() => toggleLocation(loc)}
                  />
                  <span>{loc}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Results Status */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Lead Results
            </Label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "all", label: "All Tasks" },
                { id: "has_results", label: "Has Results" },
                { id: "no_results", label: "No Results" },
              ].map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() =>
                    onFilterChange({
                      ...filters,
                      hasResults: r.id as TaskFilterState["hasResults"],
                    })
                  }
                  className={`py-1.5 px-2 rounded-md border text-center transition-all ${
                    filters.hasResults === r.id
                      ? "border-primary bg-primary/8 text-primary font-medium"
                      : "border-border text-muted-foreground hover:border-border/80"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Date Filter */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Timeframe
            </Label>
            <div className="grid grid-cols-2 gap-1.5">
              {DATE_OPTIONS.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() =>
                    onFilterChange({
                      ...filters,
                      dateRange: d.id,
                    })
                  }
                  className={`py-1.5 px-2 rounded-md border text-left text-[11px] transition-all ${
                    filters.dateRange === d.id
                      ? "border-primary bg-primary/8 text-primary font-medium"
                      : "border-border text-muted-foreground hover:border-border/80"
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border p-3 flex justify-end gap-2 bg-slate-50/50">
          <Button size="sm" onClick={() => setOpen(false)} className="h-8 text-xs">
            Apply Filters
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
