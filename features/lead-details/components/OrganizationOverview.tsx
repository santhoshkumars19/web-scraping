"use client";

import { Building2, Globe, MapPin, Tag, ExternalLink } from "lucide-react";
import type { Lead } from "@/types/lead";

interface OrganizationOverviewProps {
  lead: Lead;
}

export function OrganizationOverview({ lead }: OrganizationOverviewProps) {
  const getDomain = (url?: string) => {
    if (!url) return null;
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url.replace(/^https?:\/\//, "").split("/")[0];
    }
  };

  return (
    <div className="rounded-xl border border-border bg-white p-5 sm:p-6 shadow-sm">
      <div className="flex items-center gap-2 border-b border-border pb-3 mb-4">
        <Building2 className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">Organization Overview</h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        {/* Organization Name */}
        <div className="space-y-1">
          <span className="text-muted-foreground uppercase tracking-wider text-[10px] font-semibold flex items-center gap-1.5">
            <Building2 className="h-3 w-3 text-muted-foreground/70" />
            Organization Name
          </span>
          <p className="text-sm font-medium text-foreground">
            {lead.organizationName}
          </p>
        </div>

        {/* Category */}
        <div className="space-y-1">
          <span className="text-muted-foreground uppercase tracking-wider text-[10px] font-semibold flex items-center gap-1.5">
            <Tag className="h-3 w-3 text-muted-foreground/70" />
            Category
          </span>
          <p className="text-sm font-medium text-foreground">
            {lead.category}
          </p>
        </div>

        {/* Website */}
        <div className="space-y-1 sm:col-span-2">
          <span className="text-muted-foreground uppercase tracking-wider text-[10px] font-semibold flex items-center gap-1.5">
            <Globe className="h-3 w-3 text-muted-foreground/70" />
            Official Website
          </span>
          {lead.website ? (
            <a
              href={lead.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-mono text-primary hover:underline"
            >
              <span>{lead.website}</span>
              <ExternalLink className="h-3.5 w-3.5 opacity-70" />
            </a>
          ) : (
            <p className="text-sm text-muted-foreground/60 italic">Not available</p>
          )}
        </div>

        {/* Address */}
        <div className="space-y-1 sm:col-span-2">
          <span className="text-muted-foreground uppercase tracking-wider text-[10px] font-semibold flex items-center gap-1.5">
            <MapPin className="h-3 w-3 text-muted-foreground/70" />
            Full Address
          </span>
          {lead.address ? (
            <p className="text-sm text-foreground leading-relaxed">
              {lead.address}
            </p>
          ) : (
            <p className="text-sm text-muted-foreground/60 italic">Not available</p>
          )}
        </div>

        {/* City & State & Pincode */}
        <div className="space-y-1">
          <span className="text-muted-foreground uppercase tracking-wider text-[10px] font-semibold">
            City / Area
          </span>
          <p className="text-sm font-medium text-foreground">
            {lead.city || lead.location || "Not available"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-muted-foreground uppercase tracking-wider text-[10px] font-semibold">
            State & Pincode
          </span>
          <p className="text-sm font-medium text-foreground">
            {lead.state || lead.location} {lead.pincode ? `— ${lead.pincode}` : ""}
          </p>
        </div>
      </div>
    </div>
  );
}
