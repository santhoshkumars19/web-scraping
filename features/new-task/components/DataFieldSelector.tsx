"use client";

import { useFormContext } from "react-hook-form";
import { CheckSquare, Square, Database } from "lucide-react";
import { FormSection } from "./FormSection";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  DATA_FIELD_GROUPS,
  ALL_FIELD_IDS,
} from "@/types/task-form";
import type { ScrapingTaskFormData } from "@/types/task-form";
import { cn } from "@/lib/utils";

export function DataFieldSelector() {
  const {
    watch,
    setValue,
    formState: { errors },
  } = useFormContext<ScrapingTaskFormData>();

  const selectedFields = watch("selectedFields") ?? [];
  const totalFields = ALL_FIELD_IDS.length;
  const selectedCount = selectedFields.length;
  const allSelected = selectedCount === totalFields;

  function toggle(fieldId: string) {
    const next = selectedFields.includes(fieldId)
      ? selectedFields.filter((f) => f !== fieldId)
      : [...selectedFields, fieldId];
    setValue("selectedFields", next, { shouldValidate: true });
  }

  function selectAll() {
    setValue("selectedFields", [...ALL_FIELD_IDS], { shouldValidate: true });
  }

  function clearAll() {
    setValue("selectedFields", [], { shouldValidate: true });
  }

  return (
    <FormSection
      title="Data to Extract"
      description="Choose the information you want to collect from publicly available sources."
    >
      {/* Controls bar */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">
            {selectedCount} field{selectedCount !== 1 ? "s" : ""} selected
          </span>
          {errors.selectedFields && (
            <span className="text-xs text-destructive">
              — {errors.selectedFields.message}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={selectAll}
            disabled={allSelected}
            className="flex items-center gap-1 text-xs font-medium text-primary hover:underline disabled:opacity-40 disabled:no-underline"
          >
            <CheckSquare className="h-3.5 w-3.5" />
            Select All
          </button>
          <span className="text-muted-foreground/40">·</span>
          <button
            type="button"
            onClick={clearAll}
            disabled={selectedCount === 0}
            className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground hover:underline disabled:opacity-40 disabled:no-underline"
          >
            <Square className="h-3.5 w-3.5" />
            Clear All
          </button>
        </div>
      </div>

      {/* Field groups */}
      <div className="flex flex-col gap-6">
        {DATA_FIELD_GROUPS.map((group) => (
          <div key={group.id}>
            <p className="mb-2.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground/60">
              {group.label}
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {group.fields.map((field) => {
                const checked = selectedFields.includes(field.id);
                return (
                  <label
                    key={field.id}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm transition-colors",
                      checked
                        ? "border-primary/30 bg-primary/5 text-foreground"
                        : "border-border bg-slate-50/50 text-muted-foreground hover:border-border hover:bg-slate-50 hover:text-foreground"
                    )}
                  >
                    <Checkbox
                      checked={checked}
                      onCheckedChange={() => toggle(field.id)}
                      className="shrink-0"
                    />
                    <span className="font-medium leading-none">{field.label}</span>
                  </label>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </FormSection>
  );
}
