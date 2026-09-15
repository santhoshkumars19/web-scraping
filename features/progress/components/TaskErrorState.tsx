"use client";

import Link from "next/link";
import { AlertOctagon, RefreshCw, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TaskProgress } from "@/types/progress";

interface TaskErrorStateProps {
  task: TaskProgress;
  onRetry: () => void;
}

export function TaskErrorState({ task, onRetry }: TaskErrorStateProps) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50/40 p-6 shadow-sm mb-6">
      <div className="flex flex-col sm:flex-row items-start gap-4">
        <div className="p-3 bg-rose-500 text-white rounded-xl shadow-xs shrink-0 mt-0.5">
          <AlertOctagon className="h-6 w-6" />
        </div>

        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-bold text-rose-900">
            Scraping task failed
          </h2>
          <p className="text-sm text-rose-800/80 mt-1">
            The task could not be completed.
          </p>

          <div className="mt-4 p-3 rounded-lg bg-white/80 border border-rose-100 text-xs space-y-1.5 font-mono">
            <div className="flex gap-2">
              <span className="text-muted-foreground w-20">Task ID:</span>
              <span className="font-semibold text-foreground">{task.taskId}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-20">Target:</span>
              <span className="text-foreground">{task.keyword} in {task.location}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-20">Reason:</span>
              <span className="text-rose-700 font-sans">
                {task.failureReason || "Unable to complete the task because the discovery service was unavailable."}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 mt-5">
            <Button size="sm" onClick={onRetry} className="gap-2 bg-rose-600 hover:bg-rose-700 text-white">
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry Task</span>
            </Button>
            <Button variant="outline" size="sm" asChild className="gap-1.5 bg-white">
              <Link href="/tasks">
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Back to Tasks</span>
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
