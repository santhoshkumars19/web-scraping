"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckSquare, Square } from "lucide-react";
import type { ExportFieldId } from "@/types/export";
import {
  EXPORT_FIELD_GROUPS,
  ORDERED_EXPORT_FIELDS,
} from "@/lib/export/exportUtils";

interface ExportFieldSelectorProps {
  selectedFields: ExportFieldId[];
  onSelectedFieldsChange: (fields: ExportFieldId[]) => void;
}

export function ExportFieldSelector({
  selectedFields,
  onSelectedFieldsChange,
}: ExportFieldSelectorProps) {
  const selectedSet = new Set(selectedFields);

  const handleToggle = (fieldId: ExportFieldId) => {
    if (selectedSet.has(fieldId)) {
      onSelectedFieldsChange(selectedFields.filter((id) => id !== fieldId));
    } else {
      onSelectedFieldsChange([...selectedFields, fieldId]);
    }
  };

  const handleSelectAll = () => {
    onSelectedFieldsChange([...ORDERED_EXPORT_FIELDS]);
  };

  const handleClearAll = () => {
    onSelectedFieldsChange([]);
  };

  const handleToggleGroup = (fieldIds: ExportFieldId[]) => {
    const allGroupSelected = fieldIds.every((id) => selectedSet.has(id));
    if (allGroupSelected) {
      // Remove all in this group
      onSelectedFieldsChange(selectedFields.filter((id) => !fieldIds.includes(id)));
    } else {
      // Add all missing in this group
      const newSet = new Set(selectedFields);
      fieldIds.forEach((id) => newSet.add(id));
      onSelectedFieldsChange(Array.from(newSet));
    }
  };

  return (
    <div className="space-y-3">
      {/* Header & Quick Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 pb-2">
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-foreground uppercase tracking-wider">
            Fields
          </label>
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
              selectedFields.length > 0
                ? "bg-primary/10 text-primary font-mono"
                : "bg-rose-50 text-rose-600 border border-rose-200"
            }`}
          >
            {selectedFields.length} {selectedFields.length === 1 ? "field" : "fields"} selected
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleSelectAll}
            className="h-7 text-xs px-2 text-muted-foreground hover:text-foreground"
          >
            <CheckSquare className="h-3 w-3 mr-1" />
            Select All
          </Button>
          <span className="text-border">|</span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleClearAll}
            className="h-7 text-xs px-2 text-muted-foreground hover:text-foreground"
          >
            <Square className="h-3 w-3 mr-1" />
            Clear All
          </Button>
        </div>
      </div>

      {/* Validation warning if 0 fields */}
      {selectedFields.length === 0 && (
        <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>Select at least one field to export.</span>
        </div>
      )}

      {/* Grouped Field Sections */}
      <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
        {EXPORT_FIELD_GROUPS.map((group) => {
          const groupFieldIds = group.fields.map((f) => f.id);
          const allGroupSelected = groupFieldIds.every((id) => selectedSet.has(id));

          return (
            <div
              key={group.groupKey}
              className="rounded-lg border border-border/70 p-2.5 bg-slate-50/40"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                  {group.title}
                </span>
                <button
                  type="button"
                  onClick={() => handleToggleGroup(groupFieldIds)}
                  className="text-[10px] text-primary hover:underline font-medium"
                >
                  {allGroupSelected ? "Deselect group" : "Select group"}
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {group.fields.map((field) => {
                  const isChecked = selectedSet.has(field.id);
                  return (
                    <label
                      key={field.id}
                      className={`flex items-center gap-2 p-1.5 rounded-md text-xs cursor-pointer select-none transition-colors ${
                        isChecked
                          ? "bg-white text-foreground font-medium shadow-2xs"
                          : "text-muted-foreground hover:bg-white/60"
                      }`}
                    >
                      <Checkbox
                        checked={isChecked}
                        onCheckedChange={() => handleToggle(field.id)}
                        className="h-3.5 w-3.5"
                      />
                      <span className="truncate">{field.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
