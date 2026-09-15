"use client";

import { X } from "lucide-react";
import type { LeadFilterState, DataConfidence } from "@/types/lead";

interface ActiveFilterChipsProps {
  filters: LeadFilterState;
  onFilterChange: (filters: LeadFilterState) => void;
  onReset: () => void;
}

export function ActiveFilterChips({
  filters,
  onFilterChange,
  onReset,
}: ActiveFilterChipsProps) {
  const chips: { label: string; onRemove: () => void }[] = [];

  if (filters.search) {
    chips.push({
      label: `Search: "${filters.search}"`,
      onRemove: () => onFilterChange({ ...filters, search: "" }),
    });
  }

  filters.categories.forEach((cat) => {
    chips.push({
      label: `Category: ${cat}`,
      onRemove: () =>
        onFilterChange({
          ...filters,
          categories: filters.categories.filter((c) => c !== cat),
        }),
    });
  });

  filters.locations.forEach((loc) => {
    chips.push({
      label: `Location: ${loc}`,
      onRemove: () =>
        onFilterChange({
          ...filters,
          locations: filters.locations.filter((l) => l !== loc),
        }),
    });
  });

  filters.verifications.forEach((v: DataConfidence) => {
    chips.push({
      label: `Confidence: ${v}`,
      onRemove: () =>
        onFilterChange({
          ...filters,
          verifications: filters.verifications.filter((item) => item !== v),
        }),
    });
  });

  if (filters.hasPhone) {
    chips.push({
      label: "Has Phone",
      onRemove: () => onFilterChange({ ...filters, hasPhone: false }),
    });
  }

  if (filters.hasEmail) {
    chips.push({
      label: "Has Email",
      onRemove: () => onFilterChange({ ...filters, hasEmail: false }),
    });
  }

  if (filters.hasWebsite) {
    chips.push({
      label: "Has Website",
      onRemove: () => onFilterChange({ ...filters, hasWebsite: false }),
    });
  }

  if (filters.hasWhatsApp) {
    chips.push({
      label: "Has WhatsApp",
      onRemove: () => onFilterChange({ ...filters, hasWhatsApp: false }),
    });
  }

  if (filters.hasContactPerson) {
    chips.push({
      label: "Has Contact",
      onRemove: () => onFilterChange({ ...filters, hasContactPerson: false }),
    });
  }

  if (filters.hasSocialLinks) {
    chips.push({
      label: "Has Social",
      onRemove: () => onFilterChange({ ...filters, hasSocialLinks: false }),
    });
  }

  if (filters.taskId) {
    chips.push({
      label: `Task: ${filters.taskId}`,
      onRemove: () => onFilterChange({ ...filters, taskId: "" }),
    });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 pt-1 pb-2">
      <span className="text-xs text-muted-foreground mr-1">Active filters:</span>
      {chips.map((chip, idx) => (
        <span
          key={idx}
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/8 text-primary border border-primary/20"
        >
          <span>{chip.label}</span>
          <button
            type="button"
            onClick={chip.onRemove}
            className="hover:text-primary/70 transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}

      <button
        type="button"
        onClick={onReset}
        className="text-xs text-muted-foreground hover:text-foreground underline ml-2"
      >
        Clear all
      </button>
    </div>
  );
}
