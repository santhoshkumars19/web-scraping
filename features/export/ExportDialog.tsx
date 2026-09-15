"use client";

import { useState, useEffect, useMemo } from "react";
import { Download, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

import type { Lead } from "@/types/lead";
import type {
  ExportDialogProps,
  ExportFormat,
  ExportSourceType,
  ExportFieldId,
} from "@/types/export";
import {
  DEFAULT_SELECTED_FIELDS,
  generateDefaultFileName,
} from "@/lib/export/exportUtils";
import { runExport } from "@/lib/export/exportService";

import { ExportSourceSelector } from "./components/ExportSourceSelector";
import { ExportFormatSelector } from "./components/ExportFormatSelector";
import { ExportFieldSelector } from "./components/ExportFieldSelector";
import { ExportFileName } from "./components/ExportFileName";
import { ExportSummary } from "./components/ExportSummary";
import { ExportError } from "./components/ExportError";

export function ExportDialog({
  open,
  onOpenChange,
  allLeads = [],
  filteredLeads = [],
  selectedLeads = [],
  initialSourceType,
  initialFormat = "csv",
  initialFileName,
  taskId,
  singleLead,
  dialogTitle,
  dialogSubtitle,
  onExportComplete,
}: ExportDialogProps) {
  // Determine default source type based on provided context
  const defaultSourceType = useMemo<ExportSourceType>(() => {
    if (singleLead) return "SINGLE_LEAD";
    if (initialSourceType) return initialSourceType;
    if (selectedLeads.length > 0) return "SELECTED_LEADS";
    if (filteredLeads.length > 0 && filteredLeads.length < allLeads.length) {
      return "FILTERED_LEADS";
    }
    if (taskId) return "TASK";
    return "ALL_LEADS";
  }, [singleLead, initialSourceType, selectedLeads.length, filteredLeads.length, allLeads.length, taskId]);

  const [sourceType, setSourceType] = useState<ExportSourceType>(defaultSourceType);
  const [format, setFormat] = useState<ExportFormat>(initialFormat);
  const [selectedFields, setSelectedFields] = useState<ExportFieldId[]>(DEFAULT_SELECTED_FIELDS);

  // File Name
  const [fileName, setFileName] = useState<string>(() => {
    if (initialFileName) return initialFileName;
    return generateDefaultFileName({
      singleLeadName: singleLead?.organizationName,
      taskId,
    });
  });

  // State flags
  const [isExporting, setIsExporting] = useState(false);
  const [progressStage, setProgressStage] = useState<string>("");
  const [hasError, setHasError] = useState(false);

  // Reset or initialize when modal opens
  useEffect(() => {
    if (open) {
      setSourceType(defaultSourceType);
      setFormat(initialFormat);
      setSelectedFields(DEFAULT_SELECTED_FIELDS);
      setHasError(false);
      setProgressStage("");
      setFileName(
        initialFileName ||
          generateDefaultFileName({
            singleLeadName: singleLead?.organizationName,
            taskId,
          })
      );
    }
  }, [open, defaultSourceType, initialFormat, initialFileName, singleLead, taskId]);

  // Compute active leads to export based on selected source type
  const targetLeads = useMemo<Lead[]>(() => {
    if (singleLead) return [singleLead];
    switch (sourceType) {
      case "SELECTED_LEADS":
        return selectedLeads;
      case "FILTERED_LEADS":
        return filteredLeads.length > 0 ? filteredLeads : allLeads;
      case "TASK":
        return filteredLeads.length > 0 ? filteredLeads : allLeads;
      case "SINGLE_LEAD":
        return singleLead ? [singleLead] : [];
      case "ALL_LEADS":
      default:
        return allLeads;
    }
  }, [sourceType, singleLead, selectedLeads, filteredLeads, allLeads]);

  const recordCount = targetLeads.length;
  const isFiltered = filteredLeads.length > 0 && filteredLeads.length < allLeads.length;
  const canExport = recordCount > 0 && selectedFields.length > 0 && fileName.trim().length > 0 && !isExporting;

  // Primary action button label
  const buttonLabel = useMemo(() => {
    if (isExporting) {
      switch (progressStage) {
        case "preparing":
          return "Preparing export...";
        case "creating":
          return "Creating file...";
        case "downloading":
          return "Downloading...";
        default:
          return "Exporting...";
      }
    }
    if (recordCount === 0) return "No leads available to export";
    return `Export ${recordCount} ${recordCount === 1 ? "Lead" : "Leads"}`;
  }, [isExporting, progressStage, recordCount]);

  // Execute export
  const handleExport = async () => {
    if (!canExport) return;
    setIsExporting(true);
    setHasError(false);

    try {
      const result = await runExport(
        {
          leads: targetLeads,
          format,
          fieldIds: selectedFields,
          fileName,
          sourceType,
          taskId,
        },
        (stage) => setProgressStage(stage)
      );

      if (result.success) {
        onExportComplete?.(result.record);
        // Short delay for user to register completion before closing
        setTimeout(() => {
          setIsExporting(false);
          onOpenChange(false);
        }, 300);
      } else {
        setIsExporting(false);
        setHasError(true);
      }
    } catch {
      setIsExporting(false);
      setHasError(true);
    }
  };

  // Dynamic titles
  const computedTitle =
    dialogTitle ||
    (singleLead
      ? "Export Lead"
      : taskId
      ? "Export Task Results"
      : "Export Leads");

  const computedSubtitle =
    dialogSubtitle || "Choose what you want to export.";

  return (
    <Dialog open={open} onOpenChange={(val) => !isExporting && onOpenChange(val)}>
      <DialogContent className="sm:max-w-[760px] max-h-[92vh] overflow-y-auto p-0 gap-0">
        {/* Header */}
        <div className="p-5 border-b border-border/70 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Download className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle className="text-base font-bold text-foreground">
                {computedTitle}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                {computedSubtitle}
              </DialogDescription>
            </div>
          </div>
          <button
            type="button"
            disabled={isExporting}
            onClick={() => onOpenChange(false)}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-slate-100 disabled:opacity-50"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-5">
          {/* Error Banner if retryable */}
          {hasError && <ExportError onRetry={handleExport} />}

          {/* 1. Source Selector (hidden if single lead) */}
          <ExportSourceSelector
            sourceType={sourceType}
            onSourceTypeChange={setSourceType}
            totalCount={allLeads.length}
            filteredCount={filteredLeads.length}
            selectedCount={selectedLeads.length}
            taskId={taskId}
            singleLeadName={singleLead?.organizationName}
            isFiltered={isFiltered}
          />

          {/* 2. Format Selector */}
          <ExportFormatSelector
            format={format}
            onFormatChange={setFormat}
          />

          {/* 3. Field Selector */}
          <ExportFieldSelector
            selectedFields={selectedFields}
            onSelectedFieldsChange={setSelectedFields}
          />

          {/* 4. File Name Input */}
          <ExportFileName
            fileName={fileName}
            onFileNameChange={setFileName}
            format={format}
          />

          {/* 5. Real-time Export Summary */}
          <ExportSummary
            recordCount={recordCount}
            format={format}
            fieldCount={selectedFields.length}
            fileName={fileName}
          />
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-border flex flex-col-reverse sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="text-xs text-muted-foreground">
            {recordCount > 0 ? (
              <span>
                Ready to package {recordCount} {recordCount === 1 ? "lead" : "leads"} into {format === "excel" ? "Excel (.xlsx)" : "CSV"}.
              </span>
            ) : (
              <span className="text-rose-600 font-medium">
                No leads available to export.
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isExporting}
              onClick={() => onOpenChange(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={!canExport}
              onClick={handleExport}
              className="text-xs gap-2 min-w-[140px] bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs"
            >
              {isExporting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5" />
              )}
              <span>{buttonLabel}</span>
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
