"use client";

import { useState, useCallback, useEffect } from "react";

export type SidebarState = "expanded" | "collapsed" | "mobile-open";

interface UseSidebarReturn {
  isExpanded: boolean;
  isMobileOpen: boolean;
  toggle: () => void;
  toggleMobile: () => void;
  closeMobile: () => void;
  expand: () => void;
  collapse: () => void;
}

/**
 * Sidebar state management hook.
 *
 * - Desktop (≥1024px): persistent, togglable between expanded and collapsed icon-rail
 * - Mobile (<768px): hidden by default, opens as drawer
 * - Tablet (768–1023px): collapsed icon-rail by default
 */
export function useSidebar(): UseSidebarReturn {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Auto-collapse on tablet width
  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const handler = (e: MediaQueryListEvent) => {
      if (!e.matches) {
        setIsExpanded(false);
      } else {
        setIsExpanded(true);
      }
    };

    // Set initial state
    if (!mql.matches) {
      setIsExpanded(false);
    }

    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  // Close mobile drawer when resizing to desktop
  useEffect(() => {
    const mql = window.matchMedia("(min-width: 768px)");
    const handler = (e: MediaQueryListEvent) => {
      if (e.matches) setIsMobileOpen(false);
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  const toggle = useCallback(() => setIsExpanded((prev) => !prev), []);
  const toggleMobile = useCallback(() => setIsMobileOpen((prev) => !prev), []);
  const closeMobile = useCallback(() => setIsMobileOpen(false), []);
  const expand = useCallback(() => setIsExpanded(true), []);
  const collapse = useCallback(() => setIsExpanded(false), []);

  return {
    isExpanded,
    isMobileOpen,
    toggle,
    toggleMobile,
    closeMobile,
    expand,
    collapse,
  };
}
