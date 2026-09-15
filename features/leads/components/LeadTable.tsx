"use client";

import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { TooltipProvider } from "@/components/ui/tooltip";
import { LeadTableRow } from "./LeadTableRow";
import type {
  Lead,
  LeadSortField,
  SortDirection,
  ColumnVisibilityState,
} from "@/types/lead";

interface LeadTableProps {
  leads: Lead[];
  selectedIds: string[];
  onToggleSelectAll: () => void;
  onToggleSelectOne: (id: string, selected: boolean) => void;
  sortField: LeadSortField;
  sortDirection: SortDirection;
  onSortChange: (field: LeadSortField) => void;
  columns: ColumnVisibilityState;
  onDeleteRequest: (lead: Lead) => void;
}

export function LeadTable({
  leads,
  selectedIds,
  onToggleSelectAll,
  onToggleSelectOne,
  sortField,
  sortDirection,
  onSortChange,
  columns,
  onDeleteRequest,
}: LeadTableProps) {
  const isAllSelected =
    leads.length > 0 && leads.every((l) => selectedIds.includes(l.id));
  const isPartiallySelected =
    leads.some((l) => selectedIds.includes(l.id)) && !isAllSelected;

  const renderSortHeader = (label: string, field: LeadSortField) => {
    const isCurrent = sortField === field;
    return (
      <button
        type="button"
        onClick={() => onSortChange(field)}
        className="inline-flex items-center gap-1 hover:text-foreground transition-colors font-semibold"
      >
        <span>{label}</span>
        {isCurrent ? (
          sortDirection === "asc" ? (
            <ArrowUp className="h-3 w-3 text-primary" />
          ) : (
            <ArrowDown className="h-3 w-3 text-primary" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-30" />
        )}
      </button>
    );
  };

  return (
    <TooltipProvider delayDuration={200}>
      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-slate-50/80 text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                <th className="py-3 pl-4 pr-2 w-10">
                  <Checkbox
                    checked={isAllSelected || (isPartiallySelected ? "indeterminate" : false)}
                    onCheckedChange={onToggleSelectAll}
                    aria-label="Select all visible leads"
                  />
                </th>

                {columns.organization && (
                  <th className="py-3 px-3">
                    {renderSortHeader("Organization", "organizationName")}
                  </th>
                )}

                {columns.location && (
                  <th className="py-3 px-3">
                    {renderSortHeader("Location", "location")}
                  </th>
                )}

                {columns.phone && <th className="py-3 px-3">Phone</th>}
                {columns.email && <th className="py-3 px-3">Email</th>}
                {columns.website && <th className="py-3 px-3">Website</th>}
                {columns.address && <th className="py-3 px-3">Address</th>}
                {columns.whatsapp && <th className="py-3 px-3">WhatsApp</th>}
                {columns.contactPerson && <th className="py-3 px-3">Contact</th>}

                {columns.verification && (
                  <th className="py-3 px-3">
                    {renderSortHeader("Verification", "verification")}
                  </th>
                )}

                {columns.scrapedDate && (
                  <th className="py-3 px-3">
                    {renderSortHeader("Date", "scrapedDate")}
                  </th>
                )}

                <th className="py-3 pl-2 pr-4 text-right w-12">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border/60">
              {leads.map((lead) => (
                <LeadTableRow
                  key={lead.id}
                  lead={lead}
                  isSelected={selectedIds.includes(lead.id)}
                  onSelectChange={(selected) => onToggleSelectOne(lead.id, selected)}
                  columns={columns}
                  onDeleteRequest={onDeleteRequest}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </TooltipProvider>
  );
}
