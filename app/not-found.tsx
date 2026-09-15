"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Compass, Building2, Plus, ArrowLeft, SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  const router = useRouter();

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        {/* Brand Icon Badge */}
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-xs">
          <SearchX className="h-8 w-8 text-primary" />
        </div>

        {/* Status code & Title */}
        <span className="mt-6 inline-block font-mono text-xs font-semibold tracking-wider text-primary uppercase">
          Error 404
        </span>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          Page not found
        </h1>
        <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
          Sorry, we couldn&apos;t find the page you&apos;re looking for. It may have been moved, deleted, or never existed.
        </p>

        {/* Primary Action Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            onClick={() => router.back()}
            variant="outline"
            className="w-full sm:w-auto gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </Button>

          <Button asChild className="w-full sm:w-auto gap-2">
            <Link href="/dashboard">
              <Compass className="h-4 w-4" />
              Back to Dashboard
            </Link>
          </Button>
        </div>

        {/* Quick Links Suggestions */}
        <div className="mt-10 border-t border-border pt-6 text-left">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Looking for something else?
          </p>
          <div className="mt-3 grid grid-cols-1 gap-2">
            <Link
              href="/leads"
              className="flex items-center justify-between rounded-lg p-2.5 text-xs font-medium text-foreground hover:bg-slate-100 transition-colors border border-border/60 bg-white"
            >
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary" />
                <span>Browse Discovered Leads</span>
              </div>
              <span className="text-muted-foreground">→</span>
            </Link>
            <Link
              href="/tasks/new"
              className="flex items-center justify-between rounded-lg p-2.5 text-xs font-medium text-foreground hover:bg-slate-100 transition-colors border border-border/60 bg-white"
            >
              <div className="flex items-center gap-2">
                <Plus className="h-4 w-4 text-primary" />
                <span>Launch New Scraping Task</span>
              </div>
              <span className="text-muted-foreground">→</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

