"use client";

import Link from "next/link";
import { SearchX, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LeadNotFound() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-20 px-4">
      <div className="p-4 rounded-full bg-slate-100 text-slate-500 mb-4">
        <SearchX className="h-8 w-8" />
      </div>

      <h1 className="text-xl font-bold text-foreground">Lead not found</h1>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm">
        This lead may have been removed or the link may be invalid.
      </p>

      <div className="mt-6 flex items-center gap-3">
        <Button asChild variant="outline" size="sm" className="gap-2">
          <Link href="/leads">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Leads</span>
          </Link>
        </Button>
        <Button asChild size="sm">
          <Link href="/tasks/new">
            <span>Create New Scraping Task</span>
          </Link>
        </Button>
      </div>
    </div>
  );
}
