"use client";

import { Users, Filter, CheckSquare, Layers } from "lucide-react";
import type { ExportSourceType } from "@/types/export";

interface ExportSourceSelectorProps {
  sourceType: ExportSourceType;
  onSourceTypeChange: (type: ExportSourceType) => void;
  totalCount: number;
  filteredCount: number;
  selectedCount: number;
  taskId?: string;
  singleLeadName?: string;
  isFiltered: boolean;
}

export function ExportSourceSelector({
  sourceType,
  onSourceTypeChange,
  totalCount,
  filteredCount,
  selectedCount,
  taskId,
  singleLeadName,
  isFiltered,
}: ExportSourceSelectorProps) {
  // If single lead context, show fixed source banner
  if (singleLeadName) {
    return (
      <div className="space-y-1.5">
        <label className="text-xs font-semibold text-foreground uppercase tracking-wider">
          What would you like to export?
        </label>
        <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Users className="h-4 w-4 text-primary" />
            <div>
              <div className="text-xs font-semibold text-foreground">{singleLeadName}</div>
              <div className="text-[11px] text-muted-foreground">Individual lead record</div>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-primary bg-white px-2 py-0.5 rounded border border-primary/20">
            1 lead
          </span>
        </div>
      </div>
    );
  }

  // If task-only context
  if (taskId && sourceType === "TASK") {
    return (
      <div className="space-y-1.5">
        <label className="text-xs font-semibold text-foreground uppercase tracking-wider">
          What would you like to export?
        </label>
        <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Layers className="h-4 w-4 text-primary" />
            <div>
              <div className="text-xs font-semibold text-foreground">Task Results ({taskId})</div>
              <div className="text-[11px] text-muted-foreground">All leads collected by this scraping task</div>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-primary bg-white px-2 py-0.5 rounded border border-primary/20">
            {filteredCount || totalCount} leads
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-foreground uppercase tracking-wider">
          What would you like to export?
        </label>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {/* 1. All Leads */}
        <button
          type="button"
          onClick={() => onSourceTypeChange("ALL_LEADS")}
          className={`p-3 rounded-lg border text-left transition-all relative ${
            sourceType === "ALL_LEADS"
              ? "border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
              : "border-border text-foreground hover:bg-slate-50/70"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold">All Leads</span>
            <Users className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <div className="text-xs font-mono font-bold text-foreground">
            {totalCount} leads
          </div>
        </button>

        {/* 2. Filtered Leads */}
        <button
          type="button"
          onClick={() => onSourceTypeChange("FILTERED_LEADS")}
          className={`p-3 rounded-lg border text-left transition-all relative ${
            sourceType === "FILTERED_LEADS"
              ? "border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
              : "border-border text-foreground hover:bg-slate-50/70"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold">Filtered Leads</span>
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <div className="text-xs font-mono font-bold text-foreground">
            {filteredCount} leads
          </div>
        </button>

        {/* 3. Selected Leads */}
        <button
          type="button"
          disabled={selectedCount === 0}
          onClick={() => onSourceTypeChange("SELECTED_LEADS")}
          className={`p-3 rounded-lg border text-left transition-all relative disabled:opacity-40 disabled:cursor-not-allowed ${
            sourceType === "SELECTED_LEADS"
              ? "border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
              : "border-border text-foreground hover:bg-slate-50/70"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold">Selected Leads</span>
            <CheckSquare className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <div className="text-xs font-mono font-bold text-foreground">
            {selectedCount} leads
          </div>
        </button>
      </div>

      {/* Helper text based on selected source */}
      <div className="text-[11px] text-muted-foreground">
        {sourceType === "FILTERED_LEADS" && (
          <span>
            {isFiltered
              ? "Current filters and search will be applied."
              : "No filters active — all available leads will be included."}
          </span>
        )}
        {sourceType === "ALL_LEADS" && (
          <span>All leads in your workspace will be included.</span>
        )}
        {sourceType === "SELECTED_LEADS" && (
          <span>Only the {selectedCount} currently selected leads will be exported.</span>
        )}
      </div>
    </div>
  );
}
