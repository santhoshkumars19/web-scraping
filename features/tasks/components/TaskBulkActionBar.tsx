"use client";

import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TaskBulkActionBarProps {
  selectedCount: number;
  onDeselectAll: () => void;
  onDeleteSelected: () => void;
}

export function TaskBulkActionBar({
  selectedCount,
  onDeselectAll,
  onDeleteSelected,
}: TaskBulkActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center justify-between gap-4 p-3 bg-[#141311] border border-[#2A2824] text-white rounded-xl text-xs animate-in fade-in slide-in-from-bottom-2 duration-200 shadow-xl">
      <div className="flex items-center gap-2.5">
        <span className="rounded-md bg-primary px-2 py-0.5 font-semibold text-white font-mono text-xs">
          {selectedCount}
        </span>
        <span className="text-[#E3E0D5] font-medium">
          task{selectedCount > 1 ? "s" : ""} selected
        </span>
        <button
          onClick={onDeselectAll}
          className="text-[#A5A299] hover:text-white underline ml-2 text-[11px] transition-colors"
        >
          Deselect all
        </button>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="destructive"
          size="sm"
          onClick={onDeleteSelected}
          className="h-8 gap-1.5 text-xs"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Delete Selected</span>
        </Button>
      </div>
    </div>
  );
}
