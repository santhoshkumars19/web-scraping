"use client";

import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { TooltipProvider } from "@/components/ui/tooltip";
import { TaskTableRow } from "./TaskTableRow";
import type { TaskItem, TaskSortField, SortDirection } from "@/types/task";

interface TaskTableProps {
  tasks: TaskItem[];
  selectedIds: string[];
  onToggleSelectAll: () => void;
  onToggleSelectOne: (id: string, selected: boolean) => void;
  sortField: TaskSortField;
  sortDirection: SortDirection;
  onSortChange: (field: TaskSortField) => void;
  onCancelRequest: (task: TaskItem) => void;
  onDeleteRequest: (task: TaskItem) => void;
  onRetryRequest: (task: TaskItem) => void;
  onDuplicateRequest: (task: TaskItem) => void;
  onExportRequest?: (task: TaskItem) => void;
}

export function TaskTable({
  tasks,
  selectedIds,
  onToggleSelectAll,
  onToggleSelectOne,
  sortField,
  sortDirection,
  onSortChange,
  onCancelRequest,
  onDeleteRequest,
  onRetryRequest,
  onDuplicateRequest,
  onExportRequest,
}: TaskTableProps) {
  const isAllSelected =
    tasks.length > 0 && tasks.every((t) => selectedIds.includes(t.id));
  const isPartiallySelected =
    tasks.some((t) => selectedIds.includes(t.id)) && !isAllSelected;

  const renderSortHeader = (label: string, field: TaskSortField) => {
    const isCurrent = sortField === field;
    return (
      <button
        type="button"
        onClick={() => onSortChange(field)}
        className="inline-flex items-center gap-1 hover:text-foreground transition-colors font-semibold"
      >
        <span>{label}</span>
        {isCurrent ? (
          sortDirection === "asc" ? (
            <ArrowUp className="h-3 w-3 text-primary" />
          ) : (
            <ArrowDown className="h-3 w-3 text-primary" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-30" />
        )}
      </button>
    );
  };

  return (
    <TooltipProvider delayDuration={200}>
      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-slate-50/80 text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                <th className="py-3 pl-4 pr-2 w-10">
                  <Checkbox
                    checked={isAllSelected || (isPartiallySelected ? "indeterminate" : false)}
                    onCheckedChange={onToggleSelectAll}
                    aria-label="Select all visible tasks"
                  />
                </th>
                <th className="py-3 px-3">Task ID</th>
                <th className="py-3 px-3">{renderSortHeader("Search Target", "keyword")}</th>
                <th className="py-3 px-3">{renderSortHeader("Location", "location")}</th>
                <th className="py-3 px-3">{renderSortHeader("Results", "resultsCount")}</th>
                <th className="py-3 px-3">{renderSortHeader("Status", "status")}</th>
                <th className="py-3 px-3">Progress</th>
                <th className="py-3 px-3">{renderSortHeader("Created", "createdAt")}</th>
                <th className="py-3 px-3">{renderSortHeader("Duration", "duration")}</th>
                <th className="py-3 pl-2 pr-4 text-right w-12">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border/60">
              {tasks.map((task) => (
                <TaskTableRow
                  key={task.id}
                  task={task}
                  isSelected={selectedIds.includes(task.id)}
                  onSelectChange={(selected) => onToggleSelectOne(task.id, selected)}
                  onCancelRequest={onCancelRequest}
                  onDeleteRequest={onDeleteRequest}
                  onRetryRequest={onRetryRequest}
                  onDuplicateRequest={onDuplicateRequest}
                  onExportRequest={onExportRequest}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </TooltipProvider>
  );
}
