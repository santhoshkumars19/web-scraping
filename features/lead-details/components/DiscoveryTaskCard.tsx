"use client";

import Link from "next/link";
import { Radar, ArrowRight, Tag, MapPin, Calendar, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Lead } from "@/types/lead";

interface DiscoveryTaskCardProps {
  lead: Lead;
}

export function DiscoveryTaskCard({ lead }: DiscoveryTaskCardProps) {
  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm space-y-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground uppercase tracking-wider">
          <Radar className="h-4 w-4 text-primary" />
          <span>Discovery Task</span>
        </div>
        <span className="font-mono text-xs font-semibold text-primary bg-primary/8 px-2 py-0.5 rounded">
          {lead.taskId}
        </span>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground flex items-center gap-1">
            <Tag className="h-3 w-3" />
            Target Keyword:
          </span>
          <span className="font-medium text-foreground">{lead.category}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-muted-foreground flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            Search Location:
          </span>
          <span className="font-medium text-foreground">{lead.location}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-muted-foreground flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Scraped Date:
          </span>
          <span className="font-medium text-foreground">{lead.scrapedDate}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-muted-foreground flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            Task Status:
          </span>
          <span className="font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px]">
            Completed
          </span>
        </div>
      </div>

      <Button asChild variant="outline" size="sm" className="w-full h-8 text-xs gap-1.5 bg-white mt-2">
        <Link href={`/tasks/${lead.taskId}/progress`}>
          <span>View Task Details</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </Button>
    </div>
  );
}
