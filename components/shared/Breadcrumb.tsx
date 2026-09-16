"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

const routeLabels: Record<string, string> = {
  dashboard: "Dashboard",
  tasks: "Tasks",
  new: "New Scraping Task",
  leads: "Leads",
  settings: "Settings",
  exports: "Exports",
  profile: "Profile",
  preferences: "Preferences",
  security: "Security",
  api: "API Access",
  progress: "Progress",
};

function getLabel(segment: string): string {
  return routeLabels[segment] ?? segment.charAt(0).toUpperCase() + segment.slice(1);
}

export function Breadcrumb() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const currentLabel =
    segments.length > 0
      ? getLabel(segments[segments.length - 1])
      : "Dashboard";

  return (
    <div className="flex items-center min-w-0">
      {/* Mobile compact title */}
      <div className="flex sm:hidden items-center gap-1.5 text-xs font-semibold text-foreground min-w-0">
        <span className="truncate max-w-[130px]" title={currentLabel}>
          {currentLabel}
        </span>
      </div>

      {/* Desktop full breadcrumb trail */}
      <nav
        aria-label="Breadcrumb"
        className="hidden sm:flex items-center gap-1.5 text-sm min-w-0 overflow-hidden whitespace-nowrap"
      >
        <Link
          href="/dashboard"
          className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
          aria-label="Home"
        >
          <Home className="h-4 w-4" />
        </Link>

        {segments.map((segment, index) => {
          const href = "/" + segments.slice(0, index + 1).join("/");
          const isLast = index === segments.length - 1;
          const label = getLabel(segment);

          return (
            <span key={href} className="flex items-center gap-1.5 min-w-0 shrink-0">
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
              {isLast ? (
                <span
                  className="font-medium text-foreground truncate max-w-[140px] md:max-w-[200px]"
                  title={label}
                >
                  {label}
                </span>
              ) : (
                <Link
                  href={href}
                  className={cn(
                    "text-muted-foreground hover:text-foreground transition-colors truncate max-w-[110px] md:max-w-[160px]"
                  )}
                  title={label}
                >
                  {label}
                </Link>
              )}
            </span>
          );
        })}
      </nav>
    </div>
  );
}
