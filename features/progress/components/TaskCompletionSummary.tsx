"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, FileSpreadsheet, Download, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TaskProgress } from "@/types/progress";
import type { ExportFormat } from "@/types/export";
import { ExportDialog } from "@/features/export/ExportDialog";

interface TaskCompletionSummaryProps {
  task: TaskProgress;
}

export function TaskCompletionSummary({ task }: TaskCompletionSummaryProps) {
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>("csv");

  const handleOpenExport = (format: ExportFormat) => {
    setExportFormat(format);
    setExportModalOpen(true);
  };

  const statPills = [
    { label: "Results Discovered", value: task.resultsDiscovered },
    { label: "Websites Found", value: task.websitesFound },
    { label: "Websites Crawled", value: task.websitesCrawled },
    { label: "Phones Found", value: task.phonesFound },
    { label: "Emails Found", value: task.emailsFound },
    { label: "Duplicates Removed", value: task.duplicatesRemoved },
    { label: "Failed Websites", value: task.failedWebsites },
  ];

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-6 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-emerald-500 text-white rounded-xl shadow-xs shrink-0 mt-0.5">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">
              Your scraping task is complete.
            </h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl leading-relaxed">
              LeadScout discovered organizations, extracted publicly available information, cleaned the results, and prepared your leads.
            </p>

            <div className="flex flex-wrap gap-2 mt-4">
              {statPills.map((pill) => (
                <div
                  key={pill.label}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-emerald-100 text-xs shadow-2xs"
                >
                  <span className="font-bold text-emerald-900">{pill.value}</span>
                  <span className="text-muted-foreground">{pill.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row lg:flex-col shrink-0 gap-2.5">
          <Button asChild size="default" className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white">
            <Link href={`/leads?task=${task.taskId}`}>
              <span>View Leads</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleOpenExport("csv")}
              className="gap-1.5 text-xs flex-1 bg-white hover:bg-slate-50"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export CSV</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleOpenExport("excel")}
              className="gap-1.5 text-xs flex-1 bg-white hover:bg-slate-50"
            >
              <FileSpreadsheet className="h-3.5 w-3.5" />
              <span>Export Excel</span>
            </Button>
          </div>
        </div>
      </div>

      {/* ── Reusable Export Dialog ── */}
      <ExportDialog
        open={exportModalOpen}
        onOpenChange={setExportModalOpen}
        taskId={task.taskId}
        dialogTitle="Export Task Results"
        dialogSubtitle={`Export all leads discovered during ${task.taskId}.`}
        initialSourceType="TASK"
        initialFormat={exportFormat}
      />
    </div>
  );
}
