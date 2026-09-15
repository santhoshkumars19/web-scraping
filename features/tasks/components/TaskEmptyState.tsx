"use client";

import Link from "next/link";
import { Radar, SearchX, Plus, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TaskEmptyStateProps {
  isSearchOrFilter: boolean;
  onClearFilters?: () => void;
}

export function TaskEmptyState({
  isSearchOrFilter,
  onClearFilters,
}: TaskEmptyStateProps) {
  if (isSearchOrFilter) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-border bg-white shadow-2xs">
        <div className="p-3 bg-slate-100 rounded-full text-slate-500 mb-3">
          <SearchX className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-foreground">No matching tasks</h3>
        <p className="text-xs text-muted-foreground mt-1 max-w-sm">
          Try changing your search keywords or resetting your active status and location filters.
        </p>
        {onClearFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearFilters}
            className="mt-4 gap-1.5 text-xs"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Clear Filters</span>
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-16 text-center rounded-xl border border-dashed border-border bg-white shadow-2xs">
      <div className="p-4 bg-primary/10 rounded-2xl text-primary mb-4">
        <Radar className="h-8 w-8" />
      </div>
      <h3 className="text-lg font-bold text-foreground">No scraping tasks yet</h3>
      <p className="text-xs text-muted-foreground mt-1 max-w-sm leading-relaxed">
        Create your first task to start discovering organizations and extracting verified leads.
      </p>
      <Button asChild size="sm" className="mt-6 gap-2 bg-primary">
        <Link href="/tasks/new">
          <Plus className="h-4 w-4" />
          <span>Create Scraping Task</span>
        </Link>
      </Button>
    </div>
  );
}
