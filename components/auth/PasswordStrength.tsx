"use client";

import { useMemo } from "react";

interface PasswordStrengthProps {
  password?: string;
}

export function PasswordStrength({ password = "" }: PasswordStrengthProps) {
  const analysis = useMemo(() => {
    if (!password) {
      return { score: 0, label: "", color: "bg-slate-200" };
    }

    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;

    if (score <= 2) {
      return { score: 1, label: "Weak", color: "bg-rose-500", text: "text-rose-600" };
    }
    if (score === 3) {
      return { score: 2, label: "Medium", color: "bg-amber-500", text: "text-amber-600" };
    }
    return { score: 3, label: "Strong", color: "bg-emerald-500", text: "text-emerald-600" };
  }, [password]);

  if (!password) return null;

  return (
    <div className="space-y-1.5 pt-1">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-muted-foreground">Password strength</span>
        <span className={`font-semibold ${analysis.text}`}>{analysis.label}</span>
      </div>

      <div className="grid grid-cols-3 gap-1.5">
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${
            analysis.score >= 1 ? analysis.color : "bg-slate-100"
          }`}
        />
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${
            analysis.score >= 2 ? analysis.color : "bg-slate-100"
          }`}
        />
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${
            analysis.score >= 3 ? analysis.color : "bg-slate-100"
          }`}
        />
      </div>

      <div className="text-[10px] text-muted-foreground/90 leading-tight">
        Use 8+ characters with uppercase, lowercase, and a number.
      </div>
    </div>
  );
}
