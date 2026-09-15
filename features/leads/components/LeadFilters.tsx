"use client";

import { useState } from "react";
import { Filter, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { LeadFilterState, DataConfidence } from "@/types/lead";

interface LeadFiltersProps {
  filters: LeadFilterState;
  onFilterChange: (filters: LeadFilterState) => void;
  onReset: () => void;
  activeCount: number;
}

const CATEGORY_OPTIONS = [
  "CBSE School",
  "College",
  "Hospital",
  "IT Company",
  "Restaurant",
  "Law Firm",
];

const LOCATION_OPTIONS = [
  "Puducherry",
  "Chennai",
  "Coimbatore",
  "Bangalore",
  "Madurai",
];

const VERIFICATION_OPTIONS: { id: DataConfidence; label: string }[] = [
  { id: "HIGH", label: "High Confidence" },
  { id: "MEDIUM", label: "Medium Confidence" },
  { id: "LOW", label: "Low Confidence" },
];

export function LeadFilters({
  filters,
  onFilterChange,
  onReset,
  activeCount,
}: LeadFiltersProps) {
  const [open, setOpen] = useState(false);

  const toggleCategory = (cat: string) => {
    const next = filters.categories.includes(cat)
      ? filters.categories.filter((c) => c !== cat)
      : [...filters.categories, cat];
    onFilterChange({ ...filters, categories: next });
  };

  const toggleLocation = (loc: string) => {
    const next = filters.locations.includes(loc)
      ? filters.locations.filter((l) => l !== loc)
      : [...filters.locations, loc];
    onFilterChange({ ...filters, locations: next });
  };

  const toggleVerification = (v: DataConfidence) => {
    const next = filters.verifications.includes(v)
      ? filters.verifications.filter((item) => item !== v)
      : [...filters.verifications, v];
    onFilterChange({ ...filters, verifications: next });
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="default"
          className="h-10 gap-2 text-xs font-medium relative bg-white border-border"
        >
          <Filter className="h-3.5 w-3.5 text-muted-foreground" />
          <span>Filters</span>
          {activeCount > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white">
              {activeCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-80 p-0 sm:w-96 shadow-lg border-border" align="start">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-slate-50/70">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold text-foreground">Filter Leads</span>
          </div>
          {activeCount > 0 && (
            <button
              onClick={onReset}
              className="flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <RotateCcw className="h-3 w-3" />
              Reset all
            </button>
          )}
        </div>

        {/* Scrollable filter list */}
        <div className="max-h-[420px] overflow-y-auto p-4 space-y-5 text-xs">
          {/* Categories */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Category
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {CATEGORY_OPTIONS.map((cat) => (
                <label
                  key={cat}
                  className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground"
                >
                  <Checkbox
                    checked={filters.categories.includes(cat)}
                    onCheckedChange={() => toggleCategory(cat)}
                  />
                  <span>{cat}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Locations */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Location
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {LOCATION_OPTIONS.map((loc) => (
                <label
                  key={loc}
                  className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground"
                >
                  <Checkbox
                    checked={filters.locations.includes(loc)}
                    onCheckedChange={() => toggleLocation(loc)}
                  />
                  <span>{loc}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Verification Status */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Data Confidence
            </Label>
            <div className="flex flex-col gap-2">
              {VERIFICATION_OPTIONS.map((v) => (
                <label
                  key={v.id}
                  className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground"
                >
                  <Checkbox
                    checked={filters.verifications.includes(v.id)}
                    onCheckedChange={() => toggleVerification(v.id)}
                  />
                  <span>{v.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Data Available Checkboxes */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-2 block uppercase tracking-wider">
              Data Available
            </Label>
            <div className="grid grid-cols-2 gap-2">
              <label className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                <Checkbox
                  checked={filters.hasPhone}
                  onCheckedChange={(checked) =>
                    onFilterChange({ ...filters, hasPhone: Boolean(checked) })
                  }
                />
                <span>Has Phone</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                <Checkbox
                  checked={filters.hasEmail}
                  onCheckedChange={(checked) =>
                    onFilterChange({ ...filters, hasEmail: Boolean(checked) })
                  }
                />
                <span>Has Email</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                <Checkbox
                  checked={filters.hasWebsite}
                  onCheckedChange={(checked) =>
                    onFilterChange({ ...filters, hasWebsite: Boolean(checked) })
                  }
                />
                <span>Has Website</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                <Checkbox
                  checked={filters.hasWhatsApp}
                  onCheckedChange={(checked) =>
                    onFilterChange({ ...filters, hasWhatsApp: Boolean(checked) })
                  }
                />
                <span>Has WhatsApp</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                <Checkbox
                  checked={filters.hasContactPerson}
                  onCheckedChange={(checked) =>
                    onFilterChange({ ...filters, hasContactPerson: Boolean(checked) })
                  }
                />
                <span>Has Contact Person</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                <Checkbox
                  checked={filters.hasSocialLinks}
                  onCheckedChange={(checked) =>
                    onFilterChange({ ...filters, hasSocialLinks: Boolean(checked) })
                  }
                />
                <span>Has Social Links</span>
              </label>
            </div>
          </div>

          <div className="h-px bg-border/60" />

          {/* Scraping Task ID Filter */}
          <div>
            <Label className="text-xs font-semibold text-foreground mb-1.5 block uppercase tracking-wider">
              Scraping Task ID
            </Label>
            <Input
              type="text"
              placeholder="e.g. TASK-000124"
              value={filters.taskId}
              onChange={(e) => onFilterChange({ ...filters, taskId: e.target.value })}
              className="h-8 text-xs font-mono"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border p-3 flex justify-end gap-2 bg-slate-50/50">
          <Button size="sm" onClick={() => setOpen(false)} className="h-8 text-xs">
            Apply Filters
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
