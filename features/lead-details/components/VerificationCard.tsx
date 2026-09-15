"use client";

import { ShieldCheck, Info, CheckCircle2, Award } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { Verification } from "@/types/lead";

interface VerificationCardProps {
  verification: Verification;
}

export function VerificationCard({ verification }: VerificationCardProps) {
  const completeness =
    verification.completenessPercentage !== undefined && verification.completenessPercentage !== null
      ? Math.round(verification.completenessPercentage)
      : Math.round((verification.fieldsFound / (verification.totalFields || 8)) * 100);

  const score = verification.score ?? completeness;

  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground uppercase tracking-wider">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span>Data Verification</span>
        </div>
        <StatusBadge status={verification.status} />
      </div>

      {/* Verification Metrics Breakdown */}
      <div className="grid grid-cols-3 gap-2 py-1 border-y border-border/60 text-center">
        <div className="p-2 rounded-lg bg-slate-50">
          <span className="text-[10px] text-muted-foreground block uppercase font-medium">Score</span>
          <span className="font-bold text-foreground text-sm font-mono">{score}/100</span>
        </div>
        <div className="p-2 rounded-lg bg-slate-50">
          <span className="text-[10px] text-muted-foreground block uppercase font-medium">Completeness</span>
          <span className="font-bold text-foreground text-sm font-mono">{completeness}%</span>
        </div>
        <div className="p-2 rounded-lg bg-slate-50">
          <span className="text-[10px] text-muted-foreground block uppercase font-medium">Consistency</span>
          <span className="font-bold text-foreground text-sm font-mono">
            {verification.consistencyScore !== undefined ? `${Math.round(verification.consistencyScore)}%` : "High"}
          </span>
        </div>
      </div>

      {verification.sourceQualityScore !== undefined && (
        <div className="flex items-center justify-between text-xs px-1">
          <span className="text-muted-foreground flex items-center gap-1">
            <Award className="h-3.5 w-3.5 text-emerald-600" /> Source Quality
          </span>
          <span className="font-semibold text-foreground font-mono">
            {Math.round(verification.sourceQualityScore)}%
          </span>
        </div>
      )}

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Confidence Coverage</span>
          <span className="font-bold text-foreground font-mono">{completeness}%</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-500"
            style={{ width: `${completeness}%` }}
          />
        </div>

        <div className="flex justify-between text-[11px] text-muted-foreground pt-0.5">
          <span>{verification.fieldsFound} fields extracted</span>
          <span>{verification.totalFields || 8} total standard fields</span>
        </div>
      </div>

      <div className="p-2.5 rounded-lg bg-slate-50 border border-border/60 text-[11px] text-muted-foreground flex items-start gap-2 leading-relaxed">
        <Info className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
        <span>
          Verification assessment is calculated by the backend verification engine based on public provenance and multi-source consistency.
        </span>
      </div>
    </div>
  );
}
