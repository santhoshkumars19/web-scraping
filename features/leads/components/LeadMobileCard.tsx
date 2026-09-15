"use client";

import Link from "next/link";
import { Phone, Mail, MapPin, MoreHorizontal, Eye, Copy, ExternalLink, Trash2 } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusBadge } from "@/components/shared/StatusBadge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import type { Lead } from "@/types/lead";

interface LeadMobileCardProps {
  lead: Lead;
  isSelected: boolean;
  onSelectChange: (selected: boolean) => void;
  onDeleteRequest: (lead: Lead) => void;
}

export function LeadMobileCard({
  lead,
  isSelected,
  onSelectChange,
  onDeleteRequest,
}: LeadMobileCardProps) {
  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied.`);
  };

  return (
    <div
      className={`rounded-xl border border-border p-4 bg-white transition-all shadow-2xs ${
        isSelected ? "border-primary/50 bg-primary/5" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <div className="pt-0.5">
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => onSelectChange(Boolean(checked))}
              aria-label={`Select ${lead.organizationName}`}
            />
          </div>
          <div className="min-w-0">
            <Link
              href={`/leads/${lead.id}`}
              className="text-sm font-semibold text-foreground hover:text-primary transition-colors block truncate"
            >
              {lead.organizationName}
            </Link>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
              <span>{lead.category}</span>
              <span>·</span>
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {lead.location}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <StatusBadge status={lead.verification.status} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-slate-100"
              >
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Actions</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40 text-xs">
              <DropdownMenuItem asChild>
                <Link href={`/leads/${lead.id}`} className="flex items-center gap-2">
                  <Eye className="h-3.5 w-3.5" />
                  <span>View Details</span>
                </Link>
              </DropdownMenuItem>

              {lead.phone && (
                <DropdownMenuItem onClick={() => copyText(lead.phone!, "Phone number")}>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy Phone</span>
                </DropdownMenuItem>
              )}

              {lead.email && (
                <DropdownMenuItem onClick={() => copyText(lead.email!, "Email address")}>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy Email</span>
                </DropdownMenuItem>
              )}

              {lead.website && (
                <DropdownMenuItem onClick={() => window.open(lead.website, "_blank", "noopener,noreferrer")}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>Open Website</span>
                </DropdownMenuItem>
              )}

              <DropdownMenuSeparator />

              <DropdownMenuItem
                onClick={() => onDeleteRequest(lead)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete Lead</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Contact info snippets */}
      <div className="mt-3 pt-3 border-t border-border/60 flex flex-col gap-1.5 text-xs text-muted-foreground">
        {lead.phone && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-mono text-foreground">
              <Phone className="h-3 w-3 text-muted-foreground" />
              <span>{lead.phone}</span>
            </div>
            <button
              onClick={() => copyText(lead.phone!, "Phone number")}
              className="text-[11px] text-primary hover:underline"
            >
              Copy
            </button>
          </div>
        )}

        {lead.email && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 truncate max-w-[80%] text-foreground">
              <Mail className="h-3 w-3 text-muted-foreground shrink-0" />
              <span className="truncate">{lead.email}</span>
            </div>
            <button
              onClick={() => copyText(lead.email!, "Email address")}
              className="text-[11px] text-primary hover:underline shrink-0"
            >
              Copy
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
