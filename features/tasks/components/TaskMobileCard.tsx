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
  MapPin,
  Tag,
  Calendar,
  Clock,
  ArrowRight,
  Download,
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { TaskItem } from "@/types/task";

interface TaskMobileCardProps {
  task: TaskItem;
  isSelected: boolean;
  onSelectChange: (selected: boolean) => void;
  onCancelRequest: (task: TaskItem) => void;
  onDeleteRequest: (task: TaskItem) => void;
  onRetryRequest: (task: TaskItem) => void;
  onDuplicateRequest: (task: TaskItem) => void;
  onExportRequest?: (task: TaskItem) => void;
}

export function TaskMobileCard({
  task,
  isSelected,
  onSelectChange,
  onCancelRequest,
  onDeleteRequest,
  onRetryRequest,
  onDuplicateRequest,
  onExportRequest,
}: TaskMobileCardProps) {
  const router = useRouter();

  return (
    <div
      onClick={() => router.push(`/tasks/${task.id}/progress`)}
      className={`rounded-xl border border-border p-4 bg-white transition-all shadow-2xs cursor-pointer ${
        isSelected ? "border-primary/50 bg-primary/5" : "hover:border-border/80"
      }`}
    >
      {/* Top: Checkbox, Task ID & Status */}
      <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <Checkbox
            checked={isSelected}
            onCheckedChange={(checked) => onSelectChange(Boolean(checked))}
            aria-label={`Select ${task.id}`}
          />
          <span className="font-mono text-xs font-bold text-primary">
            {task.id}
          </span>
        </div>

        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          <StatusBadge status={task.status} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="p-1 text-muted-foreground hover:text-foreground rounded-md hover:bg-slate-100"
              >
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Actions</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40 text-xs">
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
                    <span>View Leads</span>
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
        </div>
      </div>

      {/* Main Target & Location */}
      <div className="py-3 space-y-1">
        <h4 className="text-sm font-bold text-foreground truncate">
          {task.keyword}
        </h4>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <MapPin className="h-3.5 w-3.5 text-muted-foreground/70" />
          <span>{task.location}</span>
          <span>•</span>
          <span className="font-mono text-[11px]">{task.searchRadius} km</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-slate-50 border border-border/60 text-xs mb-3">
        <div>
          <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
            Results
          </span>
          <span className="font-bold text-foreground font-mono">
            {task.resultsCount} leads
          </span>
        </div>
        <div>
          <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
            Verified
          </span>
          <span className="font-bold text-emerald-700 font-mono">
            {task.verifiedCount} verified
          </span>
        </div>
      </div>

      {/* Progress Bar (if running) */}
      {task.status === "RUNNING" && (
        <div className="mb-3 space-y-1">
          <div className="flex justify-between text-[11px] font-mono text-primary">
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Bottom Footer & Action */}
      <div className="flex items-center justify-between pt-2 border-t border-border/60 text-xs text-muted-foreground">
        <div className="flex items-center gap-2 text-[11px]">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {task.duration}
          </span>
        </div>

        <Button
          size="sm"
          variant="ghost"
          asChild
          className="h-7 text-xs gap-1 text-primary hover:text-primary"
          onClick={(e) => e.stopPropagation()}
        >
          <Link href={`/tasks/${task.id}/progress`}>
            <span>View Task</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
