"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  Info,
  Download,
  CheckCheck,
  Trash2,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  type: "success" | "warning" | "info" | "export";
  href?: string;
}

const DEFAULT_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "notif-1",
    title: "Task Completed",
    message: "TASK-000124 completed • 61 verified leads extracted from Puducherry CBSE schools.",
    timestamp: "12m ago",
    read: false,
    type: "success",
    href: "/tasks/TASK-000124/progress",
  },
  {
    id: "notif-2",
    title: "Export Ready",
    message: "puducherry-schools-leads.xlsx has been generated and is ready for download.",
    timestamp: "45m ago",
    read: false,
    type: "export",
    href: "/exports",
  },
  {
    id: "notif-3",
    title: "Scraping Alert",
    message: "Task TASK-000128: 2 domains encountered connection timeouts during crawling.",
    timestamp: "3h ago",
    read: false,
    type: "warning",
    href: "/tasks",
  },
  {
    id: "notif-4",
    title: "System Update",
    message: "LeadScout crawler extraction engine updated with improved phone & WhatsApp detection.",
    timestamp: "1d ago",
    read: true,
    type: "info",
  },
];

const NOTIFICATIONS_STORAGE_KEY = "leadscout_notifications_feed";

export function NotificationButton() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "unread">("all");
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Load notifications from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
      if (stored) {
        setNotifications(JSON.parse(stored));
      } else {
        setNotifications(DEFAULT_NOTIFICATIONS);
        localStorage.setItem(
          NOTIFICATIONS_STORAGE_KEY,
          JSON.stringify(DEFAULT_NOTIFICATIONS)
        );
      }
    } catch {
      setNotifications(DEFAULT_NOTIFICATIONS);
    }
  }, []);

  const saveNotifications = (items: NotificationItem[]) => {
    setNotifications(items);
    try {
      localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(items));
    } catch {}
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleMarkAllAsRead = () => {
    const updated = notifications.map((n) => ({ ...n, read: true }));
    saveNotifications(updated);
  };

  const handleClearAll = () => {
    saveNotifications([]);
  };

  const handleItemClick = (item: NotificationItem) => {
    // Mark this one as read
    const updated = notifications.map((n) =>
      n.id === item.id ? { ...n, read: true } : n
    );
    saveNotifications(updated);
    setIsOpen(false);
    if (item.href) {
      router.push(item.href);
    }
  };

  const displayedNotifications =
    activeTab === "unread"
      ? notifications.filter((n) => !n.read)
      : notifications;

  const getIcon = (type: NotificationItem["type"]) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
      case "export":
        return <Download className="h-4 w-4 text-primary" />;
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-amber-600" />;
      case "info":
      default:
        return <Info className="h-4 w-4 text-[#0E0E0E]" />;
    }
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative focus-visible:ring-2 focus-visible:ring-primary"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4 text-slate-700" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white shadow-xs animate-in zoom-in-50">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
              <span className="sr-only">Notifications</span>
            </Button>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent>
          {unreadCount > 0
            ? `${unreadCount} unread notifications`
            : "Notifications"}
        </TooltipContent>
      </Tooltip>

      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-80 sm:w-96 p-0 shadow-xl border-border/80"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-white">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                {unreadCount} new
              </span>
            )}
          </div>
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={handleMarkAllAsRead}
              className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
            >
              <CheckCheck className="h-3.5 w-3.5" />
              <span>Mark all read</span>
            </button>
          )}
        </div>

        {/* Tab Filters */}
        <div className="flex border-b border-border/60 bg-[#F8F7F0] px-3 py-1.5 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("all")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              activeTab === "all"
                ? "bg-white text-foreground shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All ({notifications.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("unread")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              activeTab === "unread"
                ? "bg-white text-foreground shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Unread ({unreadCount})
          </button>
        </div>

        {/* Notification List */}
        <div className="max-h-[320px] overflow-y-auto divide-y divide-border/40">
          {displayedNotifications.length === 0 ? (
            <div className="py-10 text-center px-4">
              <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-muted-foreground">
                <Bell className="h-4 w-4" />
              </div>
              <p className="mt-2 text-xs font-medium text-foreground">
                {activeTab === "unread"
                  ? "No unread notifications"
                  : "No notifications"}
              </p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                {activeTab === "unread"
                  ? "You are all caught up!"
                  : "We'll notify you when scraping tasks and exports finish."}
              </p>
            </div>
          ) : (
            displayedNotifications.map((item) => (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
                className={`group flex items-start gap-3 p-3.5 transition-colors cursor-pointer ${
                  !item.read
                    ? "bg-primary/5 hover:bg-primary/10"
                    : "hover:bg-[#FAF9F5] bg-white"
                }`}
              >
                <div className="mt-0.5 shrink-0 rounded-md bg-white p-1 shadow-2xs border border-border/60">
                  {getIcon(item.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <p
                      className={`text-xs font-semibold truncate ${
                        !item.read ? "text-foreground" : "text-slate-700"
                      }`}
                    >
                      {item.title}
                    </p>
                    <span className="text-[10px] text-muted-foreground shrink-0">
                      {item.timestamp}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[11px] text-muted-foreground leading-relaxed">
                    {item.message}
                  </p>
                  {item.href && (
                    <span className="mt-1 inline-flex items-center gap-1 text-[10px] font-medium text-primary group-hover:underline">
                      View details <ExternalLink className="h-2.5 w-2.5" />
                    </span>
                  )}
                </div>
                {!item.read && (
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="flex items-center justify-between border-t border-border bg-[#F8F7F0] px-4 py-2">
            <button
              type="button"
              onClick={handleClearAll}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-destructive transition-colors"
            >
              <Trash2 className="h-3 w-3" />
              <span>Clear all</span>
            </button>
            <span className="text-[10px] text-muted-foreground">
              Updated just now
            </span>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}

