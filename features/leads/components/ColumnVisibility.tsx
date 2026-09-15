"use client";

import { Columns } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ColumnVisibilityState } from "@/types/lead";

interface ColumnVisibilityProps {
  columns: ColumnVisibilityState;
  onChange: (columns: ColumnVisibilityState) => void;
}

const COLUMN_LABELS: { key: keyof ColumnVisibilityState; label: string }[] = [
  { key: "organization", label: "Organization" },
  { key: "category", label: "Category" },
  { key: "location", label: "Location" },
  { key: "phone", label: "Phone" },
  { key: "email", label: "Email" },
  { key: "website", label: "Website" },
  { key: "address", label: "Address" },
  { key: "whatsapp", label: "WhatsApp" },
  { key: "contactPerson", label: "Contact Person" },
  { key: "verification", label: "Verification" },
  { key: "scrapedDate", label: "Scraped Date" },
];

export function ColumnVisibility({ columns, onChange }: ColumnVisibilityProps) {
  const toggle = (key: keyof ColumnVisibilityState) => {
    const next = { ...columns, [key]: !columns[key] };
    onChange(next);
    try {
      localStorage.setItem("leadscout_col_visibility", JSON.stringify(next));
    } catch {}
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="default"
          className="h-10 gap-2 text-xs font-medium bg-white border-border"
        >
          <Columns className="h-3.5 w-3.5 text-muted-foreground" />
          <span>Columns</span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel className="text-xs">Toggle Columns</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {COLUMN_LABELS.map((col) => (
          <DropdownMenuCheckboxItem
            key={col.key}
            checked={columns[col.key]}
            onCheckedChange={() => toggle(col.key)}
            className="text-xs"
          >
            {col.label}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
