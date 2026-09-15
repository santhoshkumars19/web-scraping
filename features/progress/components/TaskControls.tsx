"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, XCircle, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import type { ScrapingTaskStatus } from "@/types/progress";

interface TaskControlsProps {
  taskId: string;
  status: ScrapingTaskStatus;
  onCancel: () => void;
  onRetry: () => void;
  onTriggerFailure?: () => void;
}

export function TaskControls({
  taskId,
  status,
  onCancel,
  onRetry,
  onTriggerFailure,
}: TaskControlsProps) {
  const [cancelModalOpen, setCancelModalOpen] = useState(false);

  const confirmCancel = () => {
    setCancelModalOpen(false);
    onCancel();
  };

  return (
    <>
      <div className="rounded-xl border border-border bg-white p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex flex-col">
            <h3 className="text-sm font-semibold text-foreground">Task Controls</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {status === "RUNNING"
                ? "Results collected so far may change when the task finishes."
                : status === "CANCELLED"
                ? "Task was cancelled. Partial leads are preserved."
                : "Manage and inspect your scraping task."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {status === "RUNNING" && (
              <>
                <Button variant="outline" asChild size="sm" className="gap-1.5 text-xs">
                  <Link href={`/leads?task=${taskId}`}>
                    <span>View Partial Leads</span>
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCancelModalOpen(true)}
                  className="gap-1.5 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                >
                  <XCircle className="h-3.5 w-3.5" />
                  <span>Cancel Task</span>
                </Button>

                {onTriggerFailure && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onTriggerFailure}
                    className="text-[11px] text-muted-foreground/60 hover:text-muted-foreground"
                    title="Developer mock test for failure state"
                  >
                    Simulate Failure
                  </Button>
                )}
              </>
            )}

            {status === "CANCELLED" && (
              <>
                <Button variant="outline" asChild size="sm" className="gap-1.5 text-xs">
                  <Link href={`/leads?task=${taskId}`}>
                    <span>View Preserved Leads</span>
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                </Button>
                <Button size="sm" onClick={onRetry} className="gap-1.5 text-xs">
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Restart Task</span>
                </Button>
              </>
            )}

            {status === "COMPLETED" && (
              <Button asChild size="sm" className="gap-1.5 text-xs">
                <Link href={`/leads?task=${taskId}`}>
                  <span>View All Leads</span>
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Cancel Confirmation Dialog */}
      <Dialog open={cancelModalOpen} onOpenChange={setCancelModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <div className="flex items-center gap-2 text-rose-600 mb-1">
              <AlertCircle className="h-5 w-5" />
              <DialogTitle>Cancel scraping task?</DialogTitle>
            </div>
            <DialogDescription className="text-xs text-muted-foreground leading-relaxed pt-1">
              Are you sure you want to stop this task? Progress and partial leads collected so far will remain available.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 gap-2 sm:gap-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCancelModalOpen(false)}
            >
              Keep Running
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={confirmCancel}
            >
              Cancel Task
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
