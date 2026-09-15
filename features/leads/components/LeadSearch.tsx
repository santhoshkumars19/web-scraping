"use client";

import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";

interface LeadSearchProps {
  value: string;
  onChange: (val: string) => void;
  resultCount: number;
}

export function LeadSearch({ value, onChange, resultCount }: LeadSearchProps) {
  return (
    <div className="relative flex-1 min-w-[280px]">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted-foreground">
        <Search className="h-4 w-4" />
      </div>
      <Input
        type="text"
        placeholder="Search organizations, phone numbers, emails, websites, contacts..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-9 pr-20 h-10 text-sm bg-white border-border focus-visible:ring-primary/20"
      />
      <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center gap-1.5">
        {value && (
          <button
            type="button"
            onClick={() => onChange("")}
            className="p-1 text-muted-foreground hover:text-foreground rounded-full hover:bg-slate-100 transition-colors"
            title="Clear search"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
        <span className="text-[11px] font-medium text-muted-foreground/80 px-1.5 py-0.5 rounded bg-slate-100 font-mono">
          {resultCount} found
        </span>
      </div>
    </div>
  );
}
