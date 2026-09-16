"use client";

import { Check, Loader2, Circle } from "lucide-react";
import { STAGES } from "@/types/progress";
import type { TaskProgress, ScrapingStage } from "@/types/progress";

interface OverallProgressProps {
  task: TaskProgress;
}

export function OverallProgress({ task }: OverallProgressProps) {
  const currentStageIndex = STAGES.findIndex((s) => s.id === task.currentStage);
  const currentStageInfo = STAGES[currentStageIndex] || STAGES[0];

  return (
    <div className="rounded-xl sm:rounded-2xl border border-border bg-white p-4 sm:p-6 shadow-sm">
      {/* Header & Percentage */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <div>
          <h2 className="text-base font-bold tracking-tight text-foreground font-sans">Overall Progress</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {task.websitesCrawled} of {task.websitesFound || task.resultsDiscovered} websites crawled
          </p>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold tracking-tight text-primary font-mono">
            {task.progress}%
          </span>
          <span className="text-xs text-muted-foreground">completed</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-3 bg-muted rounded-full overflow-hidden mb-6">
        <div
          className="h-full bg-primary transition-all duration-700 ease-out rounded-full"
          style={{ width: `${task.progress}%` }}
        />
      </div>

      {/* Current Stage Indicator */}
      <div className="flex items-center gap-2.5 p-3 rounded-xl bg-primary/5 border border-primary/20 mb-6">
        {task.status === "COMPLETED" ? (
          <div className="h-5 w-5 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
            <Check className="h-3 w-3 stroke-[3]" />
          </div>
        ) : task.status === "FAILED" || task.status === "CANCELLED" ? (
          <div className="h-5 w-5 rounded-full bg-slate-400 text-white flex items-center justify-center shrink-0">
            <Circle className="h-3 w-3" />
          </div>
        ) : (
          <Loader2 className="h-4 w-4 text-primary animate-spin shrink-0" />
        )}
        <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
          <span className="text-xs font-semibold text-foreground">
            Current Stage:
          </span>
          <span className="text-xs text-primary font-medium">
            {currentStageInfo.label}
          </span>
          <span className="hidden sm:inline text-muted-foreground/40">·</span>
          <span className="text-xs text-muted-foreground">
            {currentStageInfo.description}
          </span>
        </div>
      </div>

      {/* 10-Stage Visual Timeline */}
      <div className="border-t border-border pt-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
          Pipeline Workflow Stages
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {STAGES.map((stage, idx) => {
            const isCompleted =
              task.status === "COMPLETED" || idx < currentStageIndex;
            const isCurrent =
              task.status === "RUNNING" && idx === currentStageIndex;
            const isUpcoming = idx > currentStageIndex && task.status !== "COMPLETED";

            return (
              <div
                key={stage.id}
                className={`relative flex items-start gap-2.5 p-2.5 rounded-lg border text-xs transition-all ${
                  isCurrent
                    ? "border-primary/40 bg-primary/5 shadow-xs"
                    : isCompleted
                    ? "border-emerald-200/80 bg-emerald-50/40 text-foreground"
                    : "border-border/60 bg-slate-50/50 text-muted-foreground opacity-60"
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <div className="h-4 w-4 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                      <Check className="h-2.5 w-2.5 stroke-[3]" />
                    </div>
                  ) : isCurrent ? (
                    <div className="h-4 w-4 rounded-full bg-primary text-white flex items-center justify-center animate-pulse">
                      <span className="h-1.5 w-1.5 rounded-full bg-white" />
                    </div>
                  ) : (
                    <div className="h-4 w-4 rounded-full border border-muted-foreground/40 flex items-center justify-center text-[10px] font-mono">
                      {idx + 1}
                    </div>
                  )}
                </div>

                <div className="flex flex-col min-w-0">
                  <span className={`font-medium truncate ${isCurrent ? "text-primary font-semibold" : ""}`}>
                    {stage.label}
                  </span>
                  <span className="text-[10px] text-muted-foreground truncate">
                    Step {idx + 1} of 10
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
