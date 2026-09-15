"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ChevronRight,
  Download,
  Copy,
  Check,
  MoreHorizontal,
  Edit,
  Trash2,
  ExternalLink,
  Building2,
  MapPin,
  Globe2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
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

interface LeadProfileHeaderProps {
  lead: Lead;
  onEdit: () => void;
  onDelete: () => void;
  onExport: () => void;
}

export function LeadProfileHeader({
  lead,
  onEdit,
  onDelete,
  onExport,
}: LeadProfileHeaderProps) {
  const [copiedLead, setCopiedLead] = useState(false);

  const copyLeadSummary = async () => {
    const lines: string[] = [
      lead.organizationName,
      `${lead.category} — ${lead.location}`,
    ];

    if (lead.phone) lines.push(`Phone: ${lead.phone}`);
    if (lead.alternatePhone) lines.push(`Alt Phone: ${lead.alternatePhone}`);
    if (lead.email) lines.push(`Email: ${lead.email}`);
    if (lead.website) lines.push(`Website: ${lead.website}`);
    if (lead.address) lines.push(`Address: ${lead.address}`);
    if (lead.contactPerson) {
      lines.push(`Contact: ${lead.contactPerson}${lead.designation ? ` (${lead.designation})` : ""}`);
    }

    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setCopiedLead(true);
      setTimeout(() => setCopiedLead(false), 2000);
      toast.success("Lead information copied.");
    } catch {
      toast.error("Failed to copy lead information.");
    }
  };

  const openSource = () => {
    const src = lead.sourcePages?.[0]?.url || lead.website;
    if (src) {
      window.open(src, "_blank", "noopener,noreferrer");
    } else {
      toast.info("No source page URL recorded for this lead.");
    }
  };

  return (
    <div className="space-y-4">
      {/* ── Breadcrumb ── */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Link href="/leads" className="hover:text-primary transition-colors">
          Leads
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
        <span className="font-medium text-foreground truncate max-w-[240px]">
          {lead.organizationName}
        </span>
      </nav>

      {/* ── Main Profile Banner Card ── */}
      <div className="rounded-xl border border-border bg-white p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          {/* Left: Avatar & Organization Name */}
          <div className="flex items-start gap-4">
            <div className="flex h-13 w-13 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Building2 className="h-6 w-6" />
            </div>

            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-extrabold tracking-[-0.03em] text-[#0E0E0E]">
                  {lead.organizationName}
                </h1>
                <StatusBadge status={lead.verification.status} />
              </div>

              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground/80">{lead.category}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  {lead.location}
                </span>
                <span>•</span>
                <span className="font-mono text-[11px] text-muted-foreground">
                  Task: {lead.taskId}
                </span>
              </div>

              <p className="flex items-center gap-1.5 text-xs text-muted-foreground/80 pt-0.5">
                <Globe2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                <span>Discovered from public web sources</span>
              </p>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={copyLeadSummary}
              className="h-9 gap-1.5 text-xs bg-white"
            >
              {copiedLead ? (
                <Check className="h-3.5 w-3.5 text-emerald-600" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
              <span>Copy Lead</span>
            </Button>

            <Button
              size="sm"
              onClick={onExport}
              className="h-9 gap-1.5 text-xs bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export Lead</span>
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 bg-white"
                  aria-label="More actions"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40 text-xs">
                <DropdownMenuItem onClick={onEdit} className="gap-2">
                  <Edit className="h-3.5 w-3.5" />
                  <span>Edit Lead</span>
                </DropdownMenuItem>

                <DropdownMenuItem onClick={openSource} className="gap-2">
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>Open Source</span>
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem
                  onClick={onDelete}
                  className="gap-2 text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Delete Lead</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </div>
  );
}
