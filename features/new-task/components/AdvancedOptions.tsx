"use client";

import { useState } from "react";
import { useFormContext, Controller } from "react-hook-form";
import { ChevronDown, ChevronUp, Settings2 } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CRAWL_DEPTH_OPTIONS } from "@/types/task-form";
import type { ScrapingTaskFormData } from "@/types/task-form";

interface SwitchRowProps {
  fieldName:
    | "followInternalLinks"
    | "prioritizeContact"
    | "prioritizeAbout"
    | "prioritizeAdmissions"
    | "prioritizeStaffManagement";
  label: string;
  description?: string;
}

function SwitchRow({ fieldName, label, description }: SwitchRowProps) {
  const { control } = useFormContext<ScrapingTaskFormData>();

  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{label}</p>
        {description && (
          <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
        )}
      </div>
      <Controller
        control={control}
        name={fieldName}
        render={({ field }) => (
          <Switch
            checked={field.value}
            onCheckedChange={field.onChange}
            aria-label={label}
          />
        )}
      />
    </div>
  );
}

export function AdvancedOptions() {
  const [open, setOpen] = useState(false);
  const { control, watch, setValue } = useFormContext<ScrapingTaskFormData>();
  const crawlDepth = watch("crawlDepth");

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="rounded-xl border border-border bg-white shadow-sm">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-slate-50/80"
          >
            <div className="flex items-center gap-2">
              <Settings2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-semibold text-foreground">
                Advanced Options
              </span>
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                Optional
              </span>
            </div>
            {open ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="border-t border-border px-5 pb-5">
            {/* Crawl depth */}
            <div className="py-4">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Maximum Crawl Depth
              </Label>
              <p className="mt-0.5 mb-3 text-xs text-muted-foreground">
                Controls how deeply the crawler follows relevant internal links.
              </p>
              <div className="flex gap-2">
                {CRAWL_DEPTH_OPTIONS.map((depth) => (
                  <button
                    key={depth}
                    type="button"
                    onClick={() => setValue("crawlDepth", depth)}
                    className={`rounded-lg border px-4 py-1.5 text-sm font-medium transition-colors ${
                      crawlDepth === depth
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-slate-50 text-muted-foreground hover:border-primary/30 hover:text-primary"
                    }`}
                  >
                    {depth}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-px bg-border" />

            {/* Toggles */}
            <div className="divide-y divide-border">
              <SwitchRow
                fieldName="followInternalLinks"
                label="Follow relevant internal links"
                description="Automatically visit linked pages within the same website."
              />

              <div className="pb-1 pt-4">
                <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground/60">
                  Prioritize Page Types
                </p>
              </div>

              <SwitchRow
                fieldName="prioritizeContact"
                label="Prioritize Contact pages"
              />
              <SwitchRow
                fieldName="prioritizeAbout"
                label="Prioritize About pages"
              />
              <SwitchRow
                fieldName="prioritizeAdmissions"
                label="Prioritize Admissions pages"
              />
              <SwitchRow
                fieldName="prioritizeStaffManagement"
                label="Prioritize Staff & Management pages"
              />
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
