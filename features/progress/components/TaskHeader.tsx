"use client";

import Link from "next/link";
import { ArrowLeft, Copy, Check } from "lucide-react";
import { useState } from "react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import type { ScrapingTaskStatus } from "@/types/progress";

interface TaskHeaderProps {
  taskId: string;
  status: ScrapingTaskStatus;
}

export function TaskHeader({ taskId, status }: TaskHeaderProps) {
  const [copied, setCopied] = useState(false);

  const copyTaskId = () => {
    navigator.clipboard.writeText(taskId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getTitle = () => {
    switch (status) {
      case "COMPLETED":
        return "Scraping completed";
      case "FAILED":
        return "Scraping task failed";
      case "CANCELLED":
        return "Scraping task cancelled";
      default:
        return "Scraping in progress";
    }
  };

  const getSubtitle = () => {
    switch (status) {
      case "COMPLETED":
        return "Lead discovery finished. All extracted leads are ready to review and export.";
      case "FAILED":
        return "The scraping task encountered an error and could not finish.";
      case "CANCELLED":
        return "This task was stopped. Partially collected leads remain accessible.";
      default:
        return "Your lead discovery task is being processed in real time.";
    }
  };

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5 mb-6">
      <div className="flex flex-col gap-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" asChild className="h-8 -ml-2 text-muted-foreground gap-1.5 hover:text-foreground shrink-0">
            <Link href="/tasks">
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Back to Tasks</span>
              <span className="sm:hidden">Back</span>
            </Link>
          </Button>
          <span className="text-muted-foreground/40 hidden sm:inline">/</span>
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-md text-xs font-mono font-medium text-foreground shrink-0 whitespace-nowrap">
            <span className="whitespace-nowrap select-all">{taskId}</span>
            <button
              onClick={copyTaskId}
              className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
              title="Copy Task ID"
              aria-label="Copy Task ID"
            >
              {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
            </button>
          </div>
          <div className="shrink-0">
            <StatusBadge status={status} />
          </div>
        </div>

        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground leading-tight">
          {getTitle()}
        </h1>
        <p className="text-xs sm:text-sm text-muted-foreground">
          {getSubtitle()}
        </p>
      </div>
    </div>
  );
}
