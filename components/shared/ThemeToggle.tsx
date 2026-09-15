"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Laptop } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function ThemeToggle() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-muted-foreground hover:text-foreground"
        aria-label="Toggle theme"
      >
        <Sun className="h-4 w-4" />
      </Button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <DropdownMenu>
      <Tooltip>
        <TooltipTrigger asChild>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
              aria-label="Toggle theme"
            >
              {isDark ? (
                <Moon className="h-4 w-4 text-amber-300 transition-transform hover:rotate-12" />
              ) : (
                <Sun className="h-4 w-4 text-[#5C5A53] transition-transform hover:rotate-45" />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenuTrigger>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <span>Theme: {theme ? theme.charAt(0).toUpperCase() + theme.slice(1) : "Light"}</span>
        </TooltipContent>
      </Tooltip>

      <DropdownMenuContent align="end" className="text-xs min-w-[130px]">
        <DropdownMenuItem
          onClick={() => setTheme("light")}
          className={`gap-2 cursor-pointer ${theme === "light" ? "font-bold text-primary" : ""}`}
        >
          <Sun className="h-3.5 w-3.5" />
          <span>Light</span>
          {theme === "light" && <span className="ml-auto text-[10px]">✓</span>}
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => setTheme("dark")}
          className={`gap-2 cursor-pointer ${theme === "dark" ? "font-bold text-primary" : ""}`}
        >
          <Moon className="h-3.5 w-3.5" />
          <span>Dark</span>
          {theme === "dark" && <span className="ml-auto text-[10px]">✓</span>}
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => setTheme("system")}
          className={`gap-2 cursor-pointer ${theme === "system" ? "font-bold text-primary" : ""}`}
        >
          <Laptop className="h-3.5 w-3.5" />
          <span>System</span>
          {theme === "system" && <span className="ml-auto text-[10px]">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
