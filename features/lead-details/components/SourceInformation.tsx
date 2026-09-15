"use client";

import { FileText, ExternalLink, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { SourcePage } from "@/types/lead";

interface SourceInformationProps {
  sourcePages?: SourcePage[];
  website?: string;
}

export function SourceInformation({ sourcePages, website }: SourceInformationProps) {
  // Synthesize sources if none explicit
  const sources: SourcePage[] =
    sourcePages && sourcePages.length > 0
      ? sourcePages
      : website
      ? [
          {
            field: "Website Domain",
            url: website,
            pageTitle: "Official Homepage",
          },
        ]
      : [];

  return (
    <div className="rounded-xl border border-border bg-white p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-border pb-3 mb-4">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Source Information</h2>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100 font-medium">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Public Web Source • Source retained</span>
        </div>
      </div>

      <p className="text-xs text-muted-foreground mb-4">
        All extracted contact attributes preserve direct attribution to the public webpage where they were discovered.
      </p>

      {sources.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/70 text-muted-foreground uppercase text-[10px] tracking-wider font-semibold">
                <th className="py-2.5 px-3">Field</th>
                <th className="py-2.5 px-3">Page Title</th>
                <th className="py-2.5 px-3">Source Page URL</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {sources.map((src, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-foreground capitalize">
                    {src.field}
                  </td>
                  <td className="py-2.5 px-3 text-muted-foreground">
                    {src.pageTitle || "Public Webpage"}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-muted-foreground max-w-[200px] truncate" title={src.url}>
                    {src.url}
                  </td>
                  <td className="py-2.5 px-3 text-right whitespace-nowrap">
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                      className="h-7 text-xs gap-1.5 text-primary hover:text-primary hover:bg-primary/10"
                    >
                      <a href={src.url} target="_blank" rel="noopener noreferrer">
                        <span>Open Source</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground italic py-2">
          No explicit source URLs recorded for this lead.
        </p>
      )}
    </div>
  );
}
