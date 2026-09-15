"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { X, Radar } from "lucide-react";
import { useSidebar } from "@/hooks/useSidebar";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { cn } from "@/lib/utils";
import { SidebarNav, mainNavItems, workspaceNavItems, settingsNavItems } from "./SidebarNav";
import { Separator } from "@/components/ui/separator";
import { UserMenu } from "@/components/shared/UserMenu";
import { BrandLogo } from "@/components/shared/BrandLogo";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

interface AppShellProps {
  children: React.ReactNode;
}

/**
 * AppShell — the main layout wrapper.
 *
 * Handles:
 * - Auth routes: render cleanly without sidebar/header
 * - Desktop: persistent sidebar (expanded or collapsed icon-rail)
 * - Mobile: sidebar hidden, accessible via mobile drawer (Dialog-like overlay)
 * - Header: always visible at top
 * - Main content area wrapped in ProtectedRoute
 */
export function AppShell({ children }: AppShellProps) {
  const { isExpanded, isMobileOpen, toggle, toggleMobile, closeMobile } = useSidebar();
  const pathname = usePathname();

  // If on an auth page, render children directly without the shell sidebar/header
  const isAuthRoute = [
    "/login",
    "/signup",
    "/forgot-password",
    "/reset-password",
  ].some((route) => pathname.startsWith(route));

  // Close mobile drawer on navigation
  useEffect(() => {
    closeMobile();
  }, [pathname, closeMobile]);

  if (isAuthRoute) {
    return (
      <TooltipProvider delayDuration={200}>
        <div className="h-full h-dvh w-full overflow-y-auto bg-background text-foreground antialiased font-sans">
          {children}
        </div>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider delayDuration={200}>
      <ProtectedRoute>
        <div className="flex h-full h-dvh w-full overflow-hidden bg-background text-foreground antialiased font-sans">
          {/* ── Desktop sidebar (persisted state, animated width) ── */}
          <Sidebar
            isExpanded={isExpanded}
            onToggle={toggle}
            className="hidden md:flex"
          />

          {/* ── Mobile drawer overlay ── */}
          {isMobileOpen && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-40 bg-black/60 md:hidden backdrop-blur-xs"
                onClick={closeMobile}
                aria-hidden="true"
              />

              {/* Drawer panel */}
              <div className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-sidebar shadow-2xl md:hidden border-r border-sidebar-border">
                {/* Drawer header */}
                <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-4">
                  <BrandLogo variant="dark" />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={closeMobile}
                    className="text-sidebar-foreground hover:text-white hover:bg-sidebar-accent"
                    aria-label="Close menu"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Drawer nav */}
                <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-2 py-4">
                  <SidebarNav items={mainNavItems} collapsed={false} />
                  <Separator className="bg-sidebar-border" />
                  <SidebarNav
                    label="Workspace"
                    items={workspaceNavItems}
                    collapsed={false}
                  />
                  <Separator className="bg-sidebar-border" />
                  <SidebarNav items={settingsNavItems} collapsed={false} />
                </nav>

                {/* Drawer user menu */}
                <div className="shrink-0 border-t border-sidebar-border px-2 py-3">
                  <UserMenu collapsed={false} />
                </div>
              </div>
            </>
          )}

          {/* ── Main area (header + content) ── */}
          <div className="flex flex-1 flex-col min-w-0 h-full overflow-hidden">
            <Header onMobileMenuOpen={toggleMobile} />
            <div
              className={cn(
                "flex-1 min-h-0 overflow-y-auto",
                "bg-background"
              )}
            >
              {children}
            </div>
          </div>
        </div>
      </ProtectedRoute>
    </TooltipProvider>
  );
}
