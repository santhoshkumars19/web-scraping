"use client";

import { useFormContext, useWatch } from "react-hook-form";
import { MapPin, Tag, Hash, FileSearch, Database } from "lucide-react";
import { SEARCH_RADIUS_OPTIONS, DATA_FIELD_GROUPS } from "@/types/task-form";
import type { ScrapingTaskFormData } from "@/types/task-form";
import { cn } from "@/lib/utils";

function SummaryRow({
  icon: Icon,
  label,
  value,
  empty,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  empty?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-2 py-2">
      <div className="flex items-center gap-2 shrink-0">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <span
        className={cn(
          "text-right text-xs font-medium max-w-[55%] truncate",
          empty ? "italic text-muted-foreground/50" : "text-foreground"
        )}
      >
        {value}
      </span>
    </div>
  );
}

export function TaskSummary() {
  const { control } = useFormContext<ScrapingTaskFormData>();

  const location = useWatch({ control, name: "location" });
  const keyword = useWatch({ control, name: "keyword" });
  const searchRadius = useWatch({ control, name: "searchRadius" });
  const maxResults = useWatch({ control, name: "maxResults" });
  const maxPagesPerSite = useWatch({ control, name: "maxPagesPerSite" });
  const selectedFields = useWatch({ control, name: "selectedFields" }) ?? [];

  const radiusLabel =
    SEARCH_RADIUS_OPTIONS.find((o) => o.value === searchRadius)?.label ?? "25 km";

  const isReady = location.trim() !== "" && keyword.trim() !== "";

  // Build a flat label map for display
  const fieldLabelMap: Record<string, string> = {};
  DATA_FIELD_GROUPS.forEach((g) =>
    g.fields.forEach((f) => {
      fieldLabelMap[f.id] = f.label;
    })
  );

  return (
    <div className="sticky top-6 rounded-xl border border-border bg-card text-card-foreground shadow-sm">
      {/* Header */}
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-sm font-semibold text-foreground">Task Summary</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Updates as you fill the form
        </p>
      </div>

      <div className="px-5 py-4">
        {/* Required fields warning */}
        {!isReady && (
          <div className="mb-3 rounded-lg bg-amber-50 border border-amber-100 px-3 py-2">
            <p className="text-xs text-amber-700 font-medium">
              Complete the required fields to start.
            </p>
          </div>
        )}

        {/* Summary rows */}
        <div className="divide-y divide-border/60">
          <SummaryRow
            icon={MapPin}
            label="Location"
            value={location || "Not set"}
            empty={!location}
          />
          <SummaryRow
            icon={Tag}
            label="Keyword"
            value={keyword || "Not set"}
            empty={!keyword}
          />
          <SummaryRow icon={MapPin} label="Radius" value={radiusLabel} />
          <SummaryRow
            icon={Hash}
            label="Max Results"
            value={String(maxResults)}
          />
          <SummaryRow
            icon={FileSearch}
            label="Pages / Site"
            value={String(maxPagesPerSite)}
          />
          <SummaryRow
            icon={Database}
            label="Fields Selected"
            value={`${selectedFields.length} of ${Object.keys(fieldLabelMap).length}`}
          />
        </div>

        {/* Selected fields chips */}
        {selectedFields.length > 0 && (
          <div className="mt-4 border-t border-border/60 pt-4">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
              Selected Data
            </p>
            <div className="flex flex-wrap gap-1.5">
              {selectedFields.slice(0, 12).map((id) => (
                <span
                  key={id}
                  className="inline-flex items-center rounded-full bg-primary/8 px-2.5 py-0.5 text-[11px] font-medium text-primary"
                >
                  {fieldLabelMap[id] ?? id}
                </span>
              ))}
              {selectedFields.length > 12 && (
                <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                  +{selectedFields.length - 12} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
