"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ExternalLink,
  Copy,
  Check,
  MoreHorizontal,
  MessageSquare,
  Eye,
  FileText,
  Trash2,
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusBadge } from "@/components/shared/StatusBadge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import type { Lead, ColumnVisibilityState } from "@/types/lead";

interface LeadTableRowProps {
  lead: Lead;
  isSelected: boolean;
  onSelectChange: (selected: boolean) => void;
  columns: ColumnVisibilityState;
  onDeleteRequest: (lead: Lead) => void;
}

export function LeadTableRow({
  lead,
  isSelected,
  onSelectChange,
  columns,
  onDeleteRequest,
}: LeadTableRowProps) {
  const [copiedPhone, setCopiedPhone] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);

  const copyToClipboard = async (text: string, label: string, type: "phone" | "email") => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === "phone") {
        setCopiedPhone(true);
        setTimeout(() => setCopiedPhone(false), 2000);
        toast.success("Phone number copied.");
      } else {
        setCopiedEmail(true);
        setTimeout(() => setCopiedEmail(false), 2000);
        toast.success("Email address copied.");
      }
    } catch {
      toast.error(`Unable to copy ${label}`);
    }
  };

  const getDomain = (url?: string) => {
    if (!url) return null;
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url.replace(/^https?:\/\//, "").split("/")[0];
    }
  };

  const openSourcePage = () => {
    const src = lead.sourcePages?.[0]?.url || lead.website;
    if (src) {
      window.open(src, "_blank", "noopener,noreferrer");
    } else {
      toast.info("No source page URL recorded for this lead.");
    }
  };

  return (
    <tr
      className={`group border-b border-border/80 transition-colors ${
        isSelected ? "bg-primary/5" : "hover:bg-[#FAF9F5]"
      }`}
    >
      {/* 1. Selection Checkbox */}
      <td className="py-3 pl-4 pr-2 w-10">
        <Checkbox
          checked={isSelected}
          onCheckedChange={(checked) => onSelectChange(Boolean(checked))}
          aria-label={`Select ${lead.organizationName}`}
        />
      </td>

      {/* 2. Organization Name & Category */}
      {columns.organization && (
        <td className="py-3 px-3 min-w-[200px] max-w-[260px]">
          <div className="flex flex-col">
            <Link
              href={`/leads/${lead.id}`}
              className="text-xs font-semibold text-foreground hover:text-primary transition-colors truncate"
              title={lead.organizationName}
            >
              {lead.organizationName}
            </Link>
            {columns.category && (
              <span className="text-[11px] text-muted-foreground truncate">
                {lead.category}
              </span>
            )}
          </div>
        </td>
      )}

      {/* 3. Location */}
      {columns.location && (
        <td className="py-3 px-3 text-xs text-muted-foreground whitespace-nowrap">
          {lead.location}
        </td>
      )}

      {/* 4. Phone */}
      {columns.phone && (
        <td className="py-3 px-3 whitespace-nowrap">
          {lead.phone ? (
            <div className="flex items-center gap-1.5 text-xs text-foreground font-mono">
              <span>{lead.phone}</span>
              <button
                type="button"
                onClick={() => copyToClipboard(lead.phone!, "phone", "phone")}
                className="text-muted-foreground hover:text-foreground transition-colors p-1"
                title="Copy phone"
              >
                {copiedPhone ? (
                  <Check className="h-3 w-3 text-emerald-600" />
                ) : (
                  <Copy className="h-3 w-3 opacity-60 group-hover:opacity-100" />
                )}
              </button>
            </div>
          ) : (
            <span className="text-xs text-muted-foreground/40 font-mono">—</span>
          )}
        </td>
      )}

      {/* 5. Email */}
      {columns.email && (
        <td className="py-3 px-3 max-w-[200px] truncate">
          {lead.email ? (
            <div className="flex items-center gap-1.5 text-xs text-foreground">
              <span className="truncate" title={lead.email}>
                {lead.email}
              </span>
              <button
                type="button"
                onClick={() => copyToClipboard(lead.email!, "email", "email")}
                className="text-muted-foreground hover:text-foreground transition-colors p-1 shrink-0"
                title="Copy email"
              >
                {copiedEmail ? (
                  <Check className="h-3 w-3 text-emerald-600" />
                ) : (
                  <Copy className="h-3 w-3 opacity-60 group-hover:opacity-100" />
                )}
              </button>
            </div>
          ) : (
            <span className="text-xs text-muted-foreground/40 font-mono">—</span>
          )}
        </td>
      )}

      {/* 6. Website */}
      {columns.website && (
        <td className="py-3 px-3 whitespace-nowrap">
          {lead.website ? (
            <a
              href={lead.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-mono"
            >
              <span>{lead.website}</span>
              <ExternalLink className="h-3 w-3 shrink-0 opacity-60" />
            </a>
          ) : (
            <span className="text-xs text-muted-foreground/40 font-mono">—</span>
          )}
        </td>
      )}

      {/* 7. Address */}
      {columns.address && (
        <td className="py-3 px-3 max-w-[180px]">
          {lead.address ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="text-xs text-muted-foreground truncate block cursor-default">
                  {lead.address}
                </span>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs text-xs">
                {lead.address}
              </TooltipContent>
            </Tooltip>
          ) : (
            <span className="text-xs text-muted-foreground/40 font-mono">—</span>
          )}
        </td>
      )}

      {/* 8. WhatsApp */}
      {columns.whatsapp && (
        <td className="py-3 px-3 whitespace-nowrap">
          {lead.whatsapp ? (
            <a
              href={`https://wa.me/${lead.whatsapp.replace(/\D/g, "")}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-medium hover:bg-emerald-100 transition-colors"
              title={`WhatsApp: ${lead.whatsapp}`}
            >
              <MessageSquare className="h-3 w-3" />
              <span>Available</span>
            </a>
          ) : (
            <span className="text-xs text-muted-foreground/40 font-mono">—</span>
          )}
        </td>
      )}

      {/* 9. Contact Person */}
      {columns.contactPerson && (
        <td className="py-3 px-3 max-w-[160px]">
          {lead.contactPerson ? (
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground truncate" title={lead.contactPerson}>
                {lead.contactPerson}
              </span>
              {lead.designation && (
                <span className="text-[10px] text-muted-foreground truncate">
                  {lead.designation}
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-muted-foreground/40 font-mono">—</span>
          )}
        </td>
      )}

      {/* 10. Verification */}
      {columns.verification && (
        <td className="py-3 px-3 whitespace-nowrap">
          <StatusBadge status={lead.verification.status} />
        </td>
      )}

      {/* 11. Scraped Date */}
      {columns.scrapedDate && (
        <td className="py-3 px-3 text-xs text-muted-foreground whitespace-nowrap">
          {lead.scrapedDate}
        </td>
      )}

      {/* 12. Actions (Three Dots) */}
      <td className="py-3 pl-2 pr-4 text-right whitespace-nowrap w-12">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-slate-100 transition-colors"
            >
              <MoreHorizontal className="h-4 w-4" />
              <span className="sr-only">Actions</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44 text-xs">
            <DropdownMenuItem asChild>
              <Link href={`/leads/${lead.id}`} className="flex items-center gap-2">
                <Eye className="h-3.5 w-3.5" />
                <span>View Details</span>
              </Link>
            </DropdownMenuItem>

            {lead.phone && (
              <DropdownMenuItem onClick={() => copyToClipboard(lead.phone!, "phone", "phone")}>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy Phone</span>
              </DropdownMenuItem>
            )}

            {lead.email && (
              <DropdownMenuItem onClick={() => copyToClipboard(lead.email!, "email", "email")}>
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

            <DropdownMenuItem onClick={openSourcePage}>
              <FileText className="h-3.5 w-3.5" />
              <span>Open Source</span>
            </DropdownMenuItem>

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
      </td>
    </tr>
  );
}
