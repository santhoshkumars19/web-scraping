"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Building2,
  ListTodo,
  Compass,
  ArrowRight,
  X,
  Settings,
  ShieldCheck,
  Key,
  Sliders,
  Download,
  Plus,
  Sparkles,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MOCK_LEADS } from "@/mock/leads";
import { loadTasksFromStorage } from "@/mock/tasks";
import type { Lead } from "@/types/lead";
import type { TaskItem } from "@/types/task";

interface NavShortcut {
  id: string;
  title: string;
  subtitle: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const STATIC_NAV_SHORTCUTS: NavShortcut[] = [
  {
    id: "nav-dash",
    title: "Dashboard",
    subtitle: "Overview of your leads and scraping activity",
    href: "/dashboard",
    icon: Compass,
  },
  {
    id: "nav-new-task",
    title: "New Scraping Task",
    subtitle: "Launch a new crawler for businesses in any location",
    href: "/tasks/new",
    icon: Plus,
    badge: "Create",
  },
  {
    id: "nav-leads",
    title: "Leads Management",
    subtitle: "Browse, filter, and export verified leads",
    href: "/leads",
    icon: Building2,
  },
  {
    id: "nav-tasks",
    title: "Task History",
    subtitle: "View and manage previous scraping jobs",
    href: "/tasks",
    icon: ListTodo,
  },
  {
    id: "nav-exports",
    title: "Exports History",
    subtitle: "Download previously generated CSV and Excel files",
    href: "/exports",
    icon: Download,
  },
  {
    id: "nav-profile",
    title: "User Profile",
    subtitle: "Manage personal details and organization info",
    href: "/settings/profile",
    icon: Settings,
  },
  {
    id: "nav-preferences",
    title: "Workspace Preferences",
    subtitle: "Set default search radius, format, and themes",
    href: "/settings/preferences",
    icon: Sliders,
  },
  {
    id: "nav-security",
    title: "Security & Sessions",
    subtitle: "Update password and review active devices",
    href: "/settings/security",
    icon: ShieldCheck,
  },
  {
    id: "nav-api",
    title: "API Keys & Integrations",
    subtitle: "Manage API tokens for external CRM feeds",
    href: "/settings/api",
    icon: Key,
  },
];

type SearchResultItem =
  | { type: "nav"; data: NavShortcut }
  | { type: "lead"; data: Lead }
  | { type: "task"; data: TaskItem };

export function SearchButton() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsContainerRef = useRef<HTMLDivElement>(null);

  // Load latest tasks from storage on open
  useEffect(() => {
    if (isOpen) {
      setTasks(loadTasksFromStorage());
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
    }
  }, [isOpen]);

  // Keyboard shortcut listener (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Filtered results
  const trimmedQuery = query.trim().toLowerCase();

  const filteredNav = useMemo(() => {
    if (!trimmedQuery) return STATIC_NAV_SHORTCUTS.slice(0, 4);
    return STATIC_NAV_SHORTCUTS.filter(
      (item) =>
        item.title.toLowerCase().includes(trimmedQuery) ||
        item.subtitle.toLowerCase().includes(trimmedQuery)
    );
  }, [trimmedQuery]);

  const filteredLeads = useMemo(() => {
    if (!trimmedQuery) return [];
    return MOCK_LEADS.filter(
      (lead) =>
        lead.organizationName.toLowerCase().includes(trimmedQuery) ||
        lead.category.toLowerCase().includes(trimmedQuery) ||
        lead.location.toLowerCase().includes(trimmedQuery) ||
        (lead.email && lead.email.toLowerCase().includes(trimmedQuery)) ||
        (lead.phone && lead.phone.toLowerCase().includes(trimmedQuery)) ||
        (lead.website && lead.website.toLowerCase().includes(trimmedQuery))
    ).slice(0, 5);
  }, [trimmedQuery]);

  const filteredTasks = useMemo(() => {
    if (!trimmedQuery) return [];
    return tasks
      .filter(
        (task) =>
          task.id.toLowerCase().includes(trimmedQuery) ||
          task.keyword.toLowerCase().includes(trimmedQuery) ||
          task.location.toLowerCase().includes(trimmedQuery) ||
          task.status.toLowerCase().includes(trimmedQuery)
      )
      .slice(0, 4);
  }, [trimmedQuery, tasks]);

  // Flattened array for unified keyboard navigation
  const allResults = useMemo<SearchResultItem[]>(() => {
    const items: SearchResultItem[] = [];
    filteredNav.forEach((item) => items.push({ type: "nav", data: item }));
    filteredLeads.forEach((item) => items.push({ type: "lead", data: item }));
    filteredTasks.forEach((item) => items.push({ type: "task", data: item }));
    return items;
  }, [filteredNav, filteredLeads, filteredTasks]);

  // Adjust selection bounds
  useEffect(() => {
    if (selectedIndex >= allResults.length) {
      setSelectedIndex(Math.max(0, allResults.length - 1));
    }
  }, [allResults.length, selectedIndex]);

  const handleSelect = (item: SearchResultItem) => {
    setIsOpen(false);
    if (item.type === "nav") {
      router.push(item.data.href);
    } else if (item.type === "lead") {
      router.push(`/leads/${item.data.id}`);
    } else if (item.type === "task") {
      router.push(`/tasks/${item.data.id}/progress`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, allResults.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev <= 0 ? allResults.length - 1 : prev - 1
      );
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (allResults[selectedIndex]) {
        handleSelect(allResults[selectedIndex]);
      }
    }
  };

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs font-normal text-muted-foreground border border-border bg-[#F8F7F0]/80 hover:bg-[#F8F7F0] hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label="Search LeadScout"
          >
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="hidden sm:inline-block pr-1 text-muted-foreground">
              Search...
            </span>
            <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-border bg-white px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground shadow-2xs">
              <span className="text-[11px]">⌘</span>K
            </kbd>
          </button>
        </TooltipTrigger>
        <TooltipContent>Search leads, tasks, and pages (⌘K)</TooltipContent>
      </Tooltip>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="w-[calc(100vw-2rem)] sm:max-w-2xl rounded-2xl p-0 gap-0 overflow-hidden border-border/80 shadow-2xl">
          <DialogTitle className="sr-only">Global Search</DialogTitle>

          {/* Search Header Bar */}
          <div className="flex items-center gap-3 border-b border-border px-4 py-3 bg-white">
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSelectedIndex(0);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Search organizations, keywords, tasks, or navigation..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="rounded p-1 text-muted-foreground hover:bg-slate-100 hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
            <kbd className="rounded border border-border bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              ESC
            </kbd>
          </div>

          {/* Search Results Area */}
          <div
            ref={resultsContainerRef}
            className="max-h-[380px] overflow-y-auto p-2 divide-y divide-border/40"
          >
            {allResults.length === 0 ? (
              <div className="py-12 text-center">
                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-muted-foreground">
                  <Search className="h-5 w-5" />
                </div>
                <h4 className="mt-3 text-sm font-semibold text-foreground">
                  No matching results found
                </h4>
                <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto">
                  We couldn&apos;t find anything matching &quot;{query}&quot;. Try searching for an organization name, city, keyword, or task ID.
                </p>
              </div>
            ) : (
              <>
                {/* Navigation Group */}
                {filteredNav.length > 0 && (
                  <div className="py-1">
                    <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Navigation & Shortcuts
                    </div>
                    <div className="space-y-0.5">
                      {filteredNav.map((item) => {
                        const globalIdx = allResults.findIndex(
                          (r) => r.type === "nav" && r.data.id === item.id
                        );
                        const isSelected = globalIdx === selectedIndex;
                        const Icon = item.icon;
                        return (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() =>
                              handleSelect({ type: "nav", data: item })
                            }
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                            className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                              isSelected
                                ? "bg-primary text-white"
                                : "hover:bg-slate-100 text-foreground"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              <div
                                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${
                                  isSelected
                                    ? "bg-white/20 text-white"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                <Icon className="h-3.5 w-3.5" />
                              </div>
                              <div className="min-w-0 truncate">
                                <p className="text-xs font-semibold truncate">
                                  {item.title}
                                </p>
                                <p
                                  className={`text-[11px] truncate ${
                                    isSelected
                                      ? "text-white/80"
                                      : "text-muted-foreground"
                                  }`}
                                >
                                  {item.subtitle}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              {item.badge && (
                                <Badge
                                  variant="secondary"
                                  className={`text-[10px] ${
                                    isSelected
                                      ? "bg-white/20 text-white"
                                      : ""
                                  }`}
                                >
                                  {item.badge}
                                </Badge>
                              )}
                              <ArrowRight
                                className={`h-3 w-3 ${
                                  isSelected ? "text-white" : "text-muted-foreground"
                                }`}
                              />
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Leads Group */}
                {filteredLeads.length > 0 && (
                  <div className="py-1">
                    <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Organizations & Leads
                    </div>
                    <div className="space-y-0.5">
                      {filteredLeads.map((lead) => {
                        const globalIdx = allResults.findIndex(
                          (r) => r.type === "lead" && r.data.id === lead.id
                        );
                        const isSelected = globalIdx === selectedIndex;
                        return (
                          <button
                            key={lead.id}
                            type="button"
                            onClick={() =>
                              handleSelect({ type: "lead", data: lead })
                            }
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                            className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                              isSelected
                                ? "bg-primary text-white"
                                : "hover:bg-slate-100 text-foreground"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              <div
                                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${
                                  isSelected
                                    ? "bg-white/20 text-white"
                                    : "bg-primary/10 text-primary"
                                }`}
                              >
                                <Building2 className="h-3.5 w-3.5" />
                              </div>
                              <div className="min-w-0 truncate">
                                <p className="text-xs font-semibold truncate">
                                  {lead.organizationName}
                                </p>
                                <p
                                  className={`text-[11px] truncate ${
                                    isSelected
                                      ? "text-white/80"
                                      : "text-muted-foreground"
                                  }`}
                                >
                                  {lead.category} • {lead.location} {lead.phone ? `• ${lead.phone}` : ""}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <span
                                className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                                  isSelected
                                    ? "bg-white/20 text-white"
                                    : lead.verification.status === "HIGH"
                                    ? "bg-emerald-50 text-emerald-700"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {lead.verification.status} Confidence
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Tasks Group */}
                {filteredTasks.length > 0 && (
                  <div className="py-1">
                    <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Scraping Tasks
                    </div>
                    <div className="space-y-0.5">
                      {filteredTasks.map((task) => {
                        const globalIdx = allResults.findIndex(
                          (r) => r.type === "task" && r.data.id === task.id
                        );
                        const isSelected = globalIdx === selectedIndex;
                        return (
                          <button
                            key={task.id}
                            type="button"
                            onClick={() =>
                              handleSelect({ type: "task", data: task })
                            }
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                            className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                              isSelected
                                ? "bg-primary text-white"
                                : "hover:bg-slate-100 text-foreground"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              <div
                                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${
                                  isSelected
                                    ? "bg-white/20 text-white"
                                    : "bg-primary/10 text-primary"
                                }`}
                              >
                                <ListTodo className="h-3.5 w-3.5" />
                              </div>
                              <div className="min-w-0 truncate">
                                <div className="flex items-center gap-1.5">
                                  <span
                                    className={`font-mono text-xs font-semibold ${
                                      isSelected
                                        ? "text-white"
                                        : "text-primary"
                                    }`}
                                  >
                                    {task.id}
                                  </span>
                                  <span className="text-xs font-medium truncate">
                                    {task.keyword}
                                  </span>
                                </div>
                                <p
                                  className={`text-[11px] truncate ${
                                    isSelected
                                      ? "text-white/80"
                                      : "text-muted-foreground"
                                  }`}
                                >
                                  {task.location} • {task.resultsCount} leads discovered
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <span
                                className={`rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${
                                  isSelected
                                    ? "bg-white/20 text-white"
                                    : task.status === "COMPLETED"
                                    ? "bg-emerald-50 text-emerald-700"
                                    : task.status === "RUNNING"
                                    ? "bg-primary/10 text-primary"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {task.status}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Dialog Footer Navigation Keys */}
          <div className="flex items-center justify-between border-t border-border bg-[#F8F7F0] px-4 py-2 text-[11px] text-muted-foreground">
            <div className="hidden sm:flex items-center gap-3">
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border bg-white px-1 font-mono text-[10px]">
                  ↑
                </kbd>
                <kbd className="rounded border border-border bg-white px-1 font-mono text-[10px]">
                  ↓
                </kbd>{" "}
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border bg-white px-1 font-mono text-[10px]">
                  ↵
                </kbd>{" "}
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border bg-white px-1 font-mono text-[10px]">
                  ESC
                </kbd>{" "}
                Close
              </span>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <Sparkles className="h-3 w-3 text-primary" />
              <span>LeadScout Global Search</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

