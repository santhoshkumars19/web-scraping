import { cn } from "@/lib/utils";
import type { TaskStatus, DataConfidence } from "@/types";

type StatusVariant = TaskStatus | DataConfidence | "online" | "offline";

interface StatusBadgeProps {
  status: StatusVariant;
  className?: string;
}

const statusConfig: Record<
  StatusVariant,
  { label: string; className: string; dotClassName: string }
> = {
  // Task statuses
  PENDING: {
    label: "Pending",
    className: "bg-muted text-muted-foreground border border-border/80",
    dotClassName: "bg-muted-foreground",
  },
  RUNNING: {
    label: "Running",
    className: "bg-primary/10 text-primary border border-primary/20",
    dotClassName: "bg-primary animate-pulse",
  },
  COMPLETED: {
    label: "Completed",
    className: "bg-emerald-50 text-emerald-800 border border-emerald-200/70",
    dotClassName: "bg-emerald-600",
  },
  FAILED: {
    label: "Failed",
    className: "bg-rose-50 text-rose-800 border border-rose-200/70",
    dotClassName: "bg-rose-600",
  },
  PAUSED: {
    label: "Paused",
    className: "bg-amber-50 text-amber-800 border border-amber-200/70",
    dotClassName: "bg-amber-600",
  },
  CANCELLED: {
    label: "Cancelled",
    className: "bg-muted text-muted-foreground border border-border/80",
    dotClassName: "bg-muted-foreground",
  },

  // Data confidence
  HIGH: {
    label: "High",
    className: "bg-emerald-50 text-emerald-800 border border-emerald-200/70",
    dotClassName: "bg-emerald-600",
  },
  MEDIUM: {
    label: "Medium",
    className: "bg-amber-50 text-amber-800 border border-amber-200/70",
    dotClassName: "bg-amber-600",
  },
  LOW: {
    label: "Low",
    className: "bg-rose-50 text-rose-800 border border-rose-200/70",
    dotClassName: "bg-rose-600",
  },

  // Generic
  online: {
    label: "Online",
    className: "bg-emerald-50 text-emerald-800 border border-emerald-200/70",
    dotClassName: "bg-emerald-600",
  },
  offline: {
    label: "Offline",
    className: "bg-muted text-muted-foreground border border-border/80",
    dotClassName: "bg-muted-foreground",
  },
};

/**
 * Status badge with square colored indicator matching the SecureFlow visual style.
 * Supports task statuses, data confidence levels, and generic states.
 */
export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.PENDING;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg px-2 py-0.5 text-xs font-medium tracking-tight",
        config.className,
        className
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-[2px] shrink-0", config.dotClassName)}
        aria-hidden="true"
      />
      {config.label}
    </span>
  );
}
