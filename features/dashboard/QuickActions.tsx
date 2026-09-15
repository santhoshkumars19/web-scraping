"use client";

import Link from "next/link";
import {
  Plus,
  Users,
  History,
  Download,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface QuickAction {
  label: string;
  description: string;
  icon: React.ElementType;
  href: string;
  accent?: boolean;
}

const actions: QuickAction[] = [
  {
    label: "Create Scraping Task",
    description: "Start a new lead discovery task",
    icon: Plus,
    href: "/tasks/new",
    accent: true,
  },
  {
    label: "View All Leads",
    description: "Browse and manage your leads",
    icon: Users,
    href: "/leads",
  },
  {
    label: "Task History",
    description: "Review past scraping tasks",
    icon: History,
    href: "/tasks",
  },
  {
    label: "Export Leads",
    description: "Download leads as CSV or Excel",
    icon: Download,
    href: "/exports",
  },
];

export function QuickActions() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-[2px] bg-primary shrink-0" aria-hidden="true" />
            <h2 className="text-lg font-extrabold tracking-[-0.03em] text-[#0E0E0E] font-sans">Quick Actions</h2>
          </div>
          <p className="mt-0.5 text-xs text-[#5C5A53] pl-3.5 border-l border-[#E3E0D5] ml-0.5">
            Instant shortcuts to core discovery and export workflows
          </p>
        </div>
      </div>

      {/* Actions grid matching SecureFlow card layout */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.href}
              href={action.href}
              className={cn(
                "group relative flex flex-col justify-between rounded-2xl border border-[#E3E0D5] bg-white p-6 shadow-xs transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md hover:border-[#BE0B31]/30",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#BE0B31]"
              )}
            >
              <div>
                {/* Clean minimalist icon */}
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#EBE8DE]/60 text-[#0E0E0E] transition-colors group-hover:bg-[#BE0B31]/10 group-hover:text-[#BE0B31]">
                  <Icon className="h-5 w-5 stroke-[1.75]" />
                </div>

                {/* Title & Description */}
                <h3 className="mt-4 text-base font-extrabold tracking-[-0.03em] text-[#0E0E0E] font-sans group-hover:text-[#BE0B31] transition-colors">
                  {action.label}
                </h3>
                <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
                  {action.description}
                </p>
              </div>

              {/* Signature SecureFlow crimson action button with white arrow */}
              <div className="mt-6 flex items-center justify-start">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white shadow-xs transition-all group-hover:scale-105 group-hover:bg-[#A5082A]">
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
