"use client";

import { Menu, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Breadcrumb } from "@/components/shared/Breadcrumb";
import { SearchButton } from "@/components/shared/SearchButton";
import { NotificationButton } from "@/components/shared/NotificationButton";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
import { UserMenu } from "@/components/shared/UserMenu";
import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface HeaderProps {
  onMobileMenuOpen: () => void;
}

export function Header({ onMobileMenuOpen }: HeaderProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-background px-4 sm:px-6">
        {/* Mobile hamburger */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onMobileMenuOpen}
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Breadcrumb / page title */}
        <div className="flex flex-1 items-center min-w-0 gap-4">
          <Breadcrumb />
          <div className="hidden xl:flex items-center gap-2 text-xs font-medium text-muted-foreground border-l border-border/80 pl-4 select-none">
            <span className="h-1.5 w-1.5 rounded-[2px] bg-primary shrink-0" aria-hidden="true" />
            <span>Free Web Scraping & Lead Discovery Platform</span>
          </div>
        </div>

        {/* Right side actions */}
        <div className="flex shrink-0 items-center gap-1">
          <SearchButton />
          <NotificationButton />
          <ThemeToggle />

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Help">
                <HelpCircle className="h-4 w-4" />
                <span className="sr-only">Help</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Help & Documentation</TooltipContent>
          </Tooltip>

          {/* Divider */}
          <div className="mx-1 h-5 w-px bg-border" />

          {/* User menu (compact, header variant) */}
          <div className="hidden sm:block">
            <UserMenu collapsed />
          </div>
        </div>
      </header>
    </TooltipProvider>
  );
}
