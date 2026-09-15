"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  MoreHorizontal,
  Eye,
  Users,
  RefreshCw,
  Copy,
  XCircle,
  Trash2,
  Info,
  Compass,
  Download,
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusBadge } from "@/components/shared/StatusBadge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { toast } from "sonner";
import type { TaskItem } from "@/types/task";

interface TaskTableRowProps {
  task: TaskItem;
  isSelected: boolean;
  onSelectChange: (selected: boolean) => void;
  onCancelRequest: (task: TaskItem) => void;
  onDeleteRequest: (task: TaskItem) => void;
  onRetryRequest: (task: TaskItem) => void;
  onDuplicateRequest: (task: TaskItem) => void;
  onExportRequest?: (task: TaskItem) => void;
}

export function TaskTableRow({
  task,
  isSelected,
  onSelectChange,
  onCancelRequest,
  onDeleteRequest,
  onRetryRequest,
  onDuplicateRequest,
  onExportRequest,
}: TaskTableRowProps) {
  const router = useRouter();

  const handleRowClick = (e: React.MouseEvent) => {
    // Avoid navigation if clicking interactive elements like checkbox or action buttons
    const target = e.target as HTMLElement;
    if (
      target.closest("button") ||
      target.closest("a") ||
      target.closest("input") ||
      target.closest('[role="checkbox"]') ||
      target.closest('[data-radix-popper-content-wrapper]')
    ) {
      return;
    }
    router.push(`/tasks/${task.id}/progress`);
  };

  return (
    <tr
      onClick={handleRowClick}
      className={`group border-b border-border/80 transition-colors cursor-pointer ${
        isSelected ? "bg-primary/5" : "hover:bg-[#FAF9F5]"
      }`}
    >
      {/* 1. Checkbox */}
      <td className="py-3 pl-4 pr-2 w-10" onClick={(e) => e.stopPropagation()}>
        <Checkbox
          checked={isSelected}
          onCheckedChange={(checked) => onSelectChange(Boolean(checked))}
          aria-label={`Select task ${task.id}`}
        />
      </td>

      {/* 2. Task ID */}
      <td className="py-3 px-3 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          <Link
            href={`/tasks/${task.id}/progress`}
            className="font-mono text-xs font-semibold text-primary hover:underline"
          >
            {task.id}
          </Link>

          {/* Quick Task Info Popover */}
          <Popover>
            <PopoverTrigger asChild onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                className="text-muted-foreground/50 hover:text-muted-foreground p-0.5"
                title="View quick details"
              >
                <Info className="h-3 w-3" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-3 text-xs space-y-2 font-sans" align="start">
              <div className="font-semibold text-foreground border-b border-border/60 pb-1.5 flex justify-between">
                <span>Task Configuration</span>
                <span className="font-mono text-primary text-[11px]">{task.id}</span>
              </div>
              <div className="space-y-1 text-[11px] text-muted-foreground">
                <div className="flex justify-between">
                  <span>Target:</span>
                  <span className="font-medium text-foreground">{task.keyword}</span>
                </div>
                <div className="flex justify-between">
                  <span>Location:</span>
                  <span className="font-medium text-foreground">{task.location} ({task.searchRadius} km)</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Limit:</span>
                  <span className="font-medium text-foreground">{task.maxResults} results ({task.maxPagesPerSite} pgs/site)</span>
                </div>
                <div className="flex justify-between">
                  <span>Operator:</span>
                  <span className="font-medium text-foreground">{task.createdBy || "System"}</span>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </td>

      {/* 3. Search (Keyword) */}
      <td className="py-3 px-3 min-w-[150px] max-w-[200px]">
        <span className="text-xs font-medium text-foreground truncate block" title={task.keyword}>
          {task.keyword}
        </span>
      </td>

      {/* 4. Location */}
      <td className="py-3 px-3 whitespace-nowrap text-xs text-muted-foreground">
        {task.location}
      </td>

      {/* 5. Results Count & Verified */}
      <td className="py-3 px-3 whitespace-nowrap">
        <div className="flex flex-col">
          <span className="text-xs font-semibold font-mono text-foreground">
            {task.resultsCount} leads
          </span>
          {task.verifiedCount > 0 && (
            <span className="text-[10px] text-emerald-600 font-medium">
              {task.verifiedCount} verified
            </span>
          )}
        </div>
      </td>

      {/* 6. Status */}
      <td className="py-3 px-3 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          <StatusBadge status={task.status} />
          {task.status === "FAILED" && task.failureReason && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="cursor-help text-rose-500">
                  <Info className="h-3 w-3" />
                </span>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs text-xs text-rose-950 bg-rose-50 border-rose-200">
                {task.failureReason}
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </td>

      {/* 7. Progress */}
      <td className="py-3 px-3 min-w-[120px]">
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="font-semibold text-foreground">{task.progress}%</span>
            {task.status === "RUNNING" && task.currentStage && (
              <span className="text-[10px] text-primary truncate max-w-[90px]" title={task.currentStage}>
                {task.currentStage}
              </span>
            )}
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                task.status === "FAILED"
                  ? "bg-rose-500"
                  : task.status === "CANCELLED"
                  ? "bg-slate-400"
                  : "bg-primary"
              }`}
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      </td>

      {/* 8. Created Date */}
      <td className="py-3 px-3 whitespace-nowrap text-xs text-muted-foreground">
        {task.createdAt}
      </td>

      {/* 9. Duration */}
      <td className="py-3 px-3 whitespace-nowrap font-mono text-xs text-muted-foreground">
        {task.status === "RUNNING" ? (
          <span className="text-primary font-sans flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            Running...
          </span>
        ) : (
          task.duration
        )}
      </td>

      {/* 10. Actions Menu */}
      <td
        className="py-3 pl-2 pr-4 text-right whitespace-nowrap w-12"
        onClick={(e) => e.stopPropagation()}
      >
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-slate-100 transition-colors"
            >
              <MoreHorizontal className="h-4 w-4" />
              <span className="sr-only">Actions</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44 text-xs">
            <DropdownMenuItem asChild>
              <Link href={`/tasks/${task.id}/progress`} className="gap-2">
                <Eye className="h-3.5 w-3.5" />
                <span>View Progress</span>
              </Link>
            </DropdownMenuItem>

            {task.resultsCount > 0 && (
              <DropdownMenuItem asChild>
                <Link href={`/leads?task=${task.id}`} className="gap-2">
                  <Users className="h-3.5 w-3.5" />
                  <span>View Leads ({task.resultsCount})</span>
                </Link>
              </DropdownMenuItem>
            )}

            {task.resultsCount > 0 && onExportRequest && (
              <DropdownMenuItem onClick={() => onExportRequest(task)} className="gap-2">
                <Download className="h-3.5 w-3.5" />
                <span>Export Results</span>
              </DropdownMenuItem>
            )}

            {task.status === "FAILED" && (
              <DropdownMenuItem onClick={() => onRetryRequest(task)} className="gap-2">
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Retry Task</span>
              </DropdownMenuItem>
            )}

            <DropdownMenuItem onClick={() => onDuplicateRequest(task)} className="gap-2">
              <Copy className="h-3.5 w-3.5" />
              <span>Duplicate Task</span>
            </DropdownMenuItem>

            {task.status === "RUNNING" && (
              <DropdownMenuItem
                onClick={() => onCancelRequest(task)}
                className="gap-2 text-rose-600 focus:text-rose-600"
              >
                <XCircle className="h-3.5 w-3.5" />
                <span>Cancel Task</span>
              </DropdownMenuItem>
            )}

            <DropdownMenuSeparator />

            <DropdownMenuItem
              onClick={() => onDeleteRequest(task)}
              className="gap-2 text-destructive focus:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete Task</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </td>
    </tr>
  );
}
