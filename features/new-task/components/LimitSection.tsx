"use client";

import { useFormContext, Controller } from "react-hook-form";
import { Hash, FileSearch } from "lucide-react";
import { FormSection } from "./FormSection";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  MAX_RESULTS_PRESETS,
  MAX_PAGES_PRESETS,
} from "@/types/task-form";
import type { ScrapingTaskFormData } from "@/types/task-form";
import { cn } from "@/lib/utils";

interface NumberFieldProps {
  label: string;
  fieldName: "maxResults" | "maxPagesPerSite";
  presets: number[];
  min: number;
  max: number;
  helper: string;
  error?: string;
  icon: React.ElementType;
}

function NumberField({
  label,
  fieldName,
  presets,
  min,
  max,
  helper,
  error,
  icon: Icon,
}: NumberFieldProps) {
  const { control, setValue, watch } = useFormContext<ScrapingTaskFormData>();
  const current = watch(fieldName);

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
        </Label>
      </div>

      {/* Preset chips + custom input */}
      <div className="flex flex-wrap items-center gap-2">
        {presets.map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => setValue(fieldName, preset, { shouldValidate: true })}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              current === preset
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-slate-50 text-muted-foreground hover:border-primary/40 hover:text-primary"
            )}
          >
            {preset}
          </button>
        ))}

        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">or</span>
          <Controller
            control={control}
            name={fieldName}
            render={({ field }) => (
              <Input
                type="number"
                min={min}
                max={max}
                className={cn(
                  "h-8 w-20 text-center text-sm",
                  error && "border-destructive focus-visible:ring-destructive"
                )}
                value={field.value}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  if (!isNaN(val)) field.onChange(val);
                }}
              />
            )}
          />
        </div>
      </div>

      {error ? (
        <p className="text-xs text-destructive">{error}</p>
      ) : (
        <p className="text-xs text-muted-foreground">{helper}</p>
      )}
    </div>
  );
}

export function LimitSection() {
  const {
    formState: { errors },
  } = useFormContext<ScrapingTaskFormData>();

  return (
    <FormSection
      title="Search & Crawling Limits"
      description="Control how many organizations and website pages should be processed."
    >
      <div className="flex flex-col gap-6">
        <NumberField
          label="Maximum Results"
          fieldName="maxResults"
          presets={MAX_RESULTS_PRESETS}
          min={1}
          max={500}
          helper="Maximum number of organizations to discover."
          error={errors.maxResults?.message}
          icon={Hash}
        />

        <div className="h-px bg-border" />

        <NumberField
          label="Maximum Pages per Website"
          fieldName="maxPagesPerSite"
          presets={MAX_PAGES_PRESETS}
          min={1}
          max={100}
          helper="Maximum number of relevant public pages to crawl on each website."
          error={errors.maxPagesPerSite?.message}
          icon={FileSearch}
        />
      </div>
    </FormSection>
  );
}
