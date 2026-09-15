"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Plus,
  Users,
  History,
  BookMarked,
  Download,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

interface NavGroupProps {
  label?: string;
  items: NavItem[];
  collapsed: boolean;
}

export const mainNavItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "New Scraping Task", href: "/tasks/new", icon: Plus },
  { label: "Leads", href: "/leads", icon: Users },
  { label: "Task History", href: "/tasks", icon: History },
];

export const workspaceNavItems: NavItem[] = [
  { label: "All Leads", href: "/leads", icon: Users },
  { label: "Saved Leads", href: "/leads/saved", icon: BookMarked },
  { label: "Exports", href: "/exports", icon: Download },
];

export const settingsNavItems: NavItem[] = [
  { label: "Settings", href: "/settings", icon: Settings },
];

function NavLink({
  item,
  collapsed,
  active,
}: {
  item: NavItem;
  collapsed: boolean;
  active: boolean;
}) {
  const Icon = item.icon;

  const linkContent = (
    <Link
      href={item.href}
      className={cn(
        "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-150",
        active
          ? "bg-primary text-white shadow-xs"
          : "text-sidebar-foreground hover:bg-sidebar-accent/80 hover:text-white",
        collapsed && "justify-center px-2"
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0 transition-colors",
          active
            ? "text-white"
            : "text-sidebar-foreground group-hover:text-white"
        )}
      />
      {!collapsed && (
        <span className="truncate leading-none">{item.label}</span>
      )}
      {!collapsed && item.badge !== undefined && (
        <span
          className={cn(
            "ml-auto flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-semibold",
            active ? "bg-white/20 text-white" : "bg-primary text-white"
          )}
        >
          {item.badge}
        </span>
      )}
    </Link>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="relative">{linkContent}</div>
        </TooltipTrigger>
        <TooltipContent side="right">{item.label}</TooltipContent>
      </Tooltip>
    );
  }

  return <div className="relative">{linkContent}</div>;
}

export function SidebarNav({ label, items, collapsed }: NavGroupProps) {
  const pathname = usePathname();

  function isActive(href: string): boolean {
    if (href === "/dashboard") return pathname === "/dashboard" || pathname === "/";
    if (href === "/tasks") return pathname === "/tasks";
    if (href === "/tasks/new") return pathname === "/tasks/new";
    return pathname.startsWith(href) && href !== "/leads" ? true : pathname === href;
  }

  return (
    <div className="flex flex-col gap-0.5">
      {label && !collapsed && (
        <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-sidebar-foreground/50">
          {label}
        </p>
      )}
      {items.map((item) => (
        <NavLink
          key={item.href}
          item={item}
          collapsed={collapsed}
          active={isActive(item.href)}
        />
      ))}
    </div>
  );
}
