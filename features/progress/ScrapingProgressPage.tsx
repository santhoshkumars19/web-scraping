"use client";

import Link from "next/link";
import { ArrowRight, WifiOff, AlertCircle } from "lucide-react";
import { useTaskProgress } from "./hooks/useTaskProgress";
import { TaskHeader } from "./components/TaskHeader";
import { TaskSearchDetails } from "./components/TaskSearchDetails";
import { ProgressMetrics } from "./components/ProgressMetrics";
import { OverallProgress } from "./components/OverallProgress";
import { LiveActivity } from "./components/LiveActivity";
import { WebsiteProcessing } from "./components/WebsiteProcessing";
import { TaskControls } from "./components/TaskControls";
import { TaskCompletionSummary } from "./components/TaskCompletionSummary";
import { TaskErrorState } from "./components/TaskErrorState";
import { TaskNotFound } from "./components/TaskNotFound";
import { Button } from "@/components/ui/button";

interface ScrapingProgressPageProps {
  taskId: string;
}

export function ScrapingProgressPage({ taskId }: ScrapingProgressPageProps) {
  const {
    task,
    activityLog,
    websites,
    notFound,
    isWsConnected,
    cancelTask,
    retryTask,
    triggerFailure,
  } = useTaskProgress(taskId);

  if (notFound) {
    return <TaskNotFound />;
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-medium">Initializing task progress…</span>
        </div>
      </div>
    );
  }

  const isCompleted = task.status === "COMPLETED";
  const isFailed = task.status === "FAILED";
  const isRunning = task.status === "RUNNING" || task.status === "PENDING";

  return (
    <div className="flex flex-col gap-6 pb-6">
      {/* Header */}
      <TaskHeader taskId={task.taskId} status={task.status} />

      {/* Subtle WS Disconnect Banner (Task still continues in backend) */}
      {!isWsConnected && isRunning && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/80 px-4 py-2.5 text-xs text-amber-900 shadow-xs animate-in fade-in duration-300">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
            </span>
            <span className="font-medium">Live updates temporarily unavailable.</span>
            <span className="text-amber-700 hidden sm:inline">
              Your scraping task continues processing in the background. Polling for updates…
            </span>
          </div>
          <WifiOff className="h-4 w-4 text-amber-600 shrink-0" />
        </div>
      )}

      {/* Partial Leads Banner if running with discovered leads */}
      {isRunning && task.resultsDiscovered > 0 && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/90 px-4 py-3 text-xs text-slate-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-primary shrink-0" />
            <span>
              <strong>{task.resultsDiscovered} leads</strong> discovered so far.
              <span className="text-muted-foreground ml-1 hidden md:inline">
                These results may change while the task is still running.
              </span>
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            asChild
            className="h-7 text-xs gap-1.5 self-start sm:self-auto bg-white hover:bg-slate-100"
          >
            <Link href={`/leads?task=${task.taskId}`}>
              <span>View Partial Leads</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </Button>
        </div>
      )}

      {/* Failure Banner if FAILED */}
      {isFailed && (
        <TaskErrorState task={task} onRetry={retryTask} />
      )}

      {/* Completion Banner if COMPLETED */}
      {isCompleted && (
        <TaskCompletionSummary task={task} />
      )}

      {/* Task Search Details Card */}
      <TaskSearchDetails task={task} />

      {/* Live Metrics Grid (8 cards) */}
      <ProgressMetrics task={task} />

      {/* Main Overall Progress & 10-Stage Pipeline */}
      <OverallProgress task={task} />

      {/* Activity & Website Processing (2 Columns on Desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LiveActivity activityLog={activityLog} />
        <WebsiteProcessing
          websites={websites}
          successfulCount={task.websitesCrawled}
          failedCount={task.failedWebsites}
          blockedCount={task.blockedWebsites}
          timeoutCount={task.timeoutWebsites}
        />
      </div>

      {/* Bottom Task Controls & Confirmation Dialog */}
      <TaskControls
        taskId={task.taskId}
        status={task.status}
        onCancel={cancelTask}
        onRetry={retryTask}
        onTriggerFailure={triggerFailure}
      />
    </div>
  );
}
