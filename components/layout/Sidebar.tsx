"use client";

import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { UserMenu } from "@/components/shared/UserMenu";
import { BrandLogo } from "@/components/shared/BrandLogo";
import { SidebarNav, mainNavItems, workspaceNavItems, settingsNavItems } from "./SidebarNav";
import { Button } from "@/components/ui/button";
import { TooltipProvider } from "@/components/ui/tooltip";

interface SidebarProps {
  isExpanded: boolean;
  onToggle: () => void;
  className?: string;
}

export function Sidebar({ isExpanded, onToggle, className }: SidebarProps) {
  const collapsed = !isExpanded;

  return (
    <TooltipProvider delayDuration={200}>
      <aside
        className={cn(
          "relative flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300 ease-in-out select-none",
          isExpanded ? "w-60" : "w-[60px]",
          className
        )}
      >
        {/* ── Logo ── */}
        <div
          className={cn(
            "flex h-14 shrink-0 items-center border-b border-sidebar-border",
            collapsed ? "justify-center px-0" : "px-4"
          )}
        >
          <BrandLogo variant={collapsed ? "icon" : "dark"} />
        </div>

        {/* ── Navigation ── */}
        <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-2 py-4">
          {/* Main nav */}
          <SidebarNav items={mainNavItems} collapsed={collapsed} />

          <Separator className="bg-sidebar-border" />

          {/* Workspace nav */}
          <SidebarNav
            label="Workspace"
            items={workspaceNavItems}
            collapsed={collapsed}
          />

          <Separator className="bg-sidebar-border" />

          {/* Settings nav */}
          <SidebarNav items={settingsNavItems} collapsed={collapsed} />
        </nav>

        {/* ── User profile ── */}
        <div className="shrink-0 border-t border-sidebar-border px-2 py-3">
          <UserMenu collapsed={collapsed} />
        </div>

        {/* ── Toggle button ── */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className={cn(
            "absolute -right-3 top-[52px] z-10 h-6 w-6 rounded-full border border-sidebar-border bg-sidebar shadow-sm transition-colors hover:bg-sidebar-accent",
            "text-sidebar-foreground hover:text-sidebar-accent-foreground"
          )}
          aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isExpanded ? (
            <PanelLeftClose className="h-3 w-3" />
          ) : (
            <PanelLeftOpen className="h-3 w-3" />
          )}
        </Button>
      </aside>
    </TooltipProvider>
  );
}
