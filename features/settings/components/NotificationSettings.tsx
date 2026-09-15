"use client";

import { useState } from "react";
import { Bell, Check, Loader2 } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import type { NotificationPreferences } from "@/types/auth";
import {
  loadNotificationPreferences,
  saveNotificationPreferences,
} from "@/lib/auth/mockAuth";

export function NotificationSettings() {
  const [notifs, setNotifs] = useState<NotificationPreferences>(() =>
    loadNotificationPreferences()
  );
  const [isSaving, setIsSaving] = useState(false);

  const handleToggle = (key: keyof NotificationPreferences, value: boolean) => {
    const updated = { ...notifs, [key]: value };
    setNotifs(updated);
    saveNotificationPreferences(updated);
  };

  const handleSaveAll = async () => {
    setIsSaving(true);
    await new Promise((res) => setTimeout(res, 300));
    saveNotificationPreferences(notifs);
    setIsSaving(false);
    toast.success("Notification settings saved.");
  };

  return (
    <div className="rounded-xl border border-border/80 bg-white p-6 shadow-2xs space-y-6">
      <div>
        <h2 className="text-base font-bold text-foreground">Notifications</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Choose which events trigger application notifications and desktop alerts.
        </p>
      </div>

      <div className="divide-y divide-border/60 text-xs">
        {/* Task Completed */}
        <div className="flex items-center justify-between py-3.5">
          <div className="space-y-0.5 pr-4">
            <div className="font-semibold text-foreground">Task completed</div>
            <div className="text-muted-foreground text-[11px]">
              Notify me when an organization scraping task finishes processing.
            </div>
          </div>
          <Switch
            checked={notifs.taskCompleted}
            onCheckedChange={(v) => handleToggle("taskCompleted", v)}
            aria-label="Toggle task completed notifications"
          />
        </div>

        {/* Task Failed */}
        <div className="flex items-center justify-between py-3.5">
          <div className="space-y-0.5 pr-4">
            <div className="font-semibold text-foreground">Task failed</div>
            <div className="text-muted-foreground text-[11px]">
              Notify me if a scraping task encounters an error or timeout.
            </div>
          </div>
          <Switch
            checked={notifs.taskFailed}
            onCheckedChange={(v) => handleToggle("taskFailed", v)}
            aria-label="Toggle task failed notifications"
          />
        </div>

        {/* Export Completed */}
        <div className="flex items-center justify-between py-3.5">
          <div className="space-y-0.5 pr-4">
            <div className="font-semibold text-foreground">Export completed</div>
            <div className="text-muted-foreground text-[11px]">
              Notify me when a CSV or Excel export is prepared and ready to download.
            </div>
          </div>
          <Switch
            checked={notifs.exportCompleted}
            onCheckedChange={(v) => handleToggle("exportCompleted", v)}
            aria-label="Toggle export completed notifications"
          />
        </div>

        {/* System Updates */}
        <div className="flex items-center justify-between py-3.5">
          <div className="space-y-0.5 pr-4">
            <div className="font-semibold text-foreground">System updates</div>
            <div className="text-muted-foreground text-[11px]">
              Receive news about new LeadScout features and algorithmic crawler improvements.
            </div>
          </div>
          <Switch
            checked={notifs.systemUpdates}
            onCheckedChange={(v) => handleToggle("systemUpdates", v)}
            aria-label="Toggle system updates notifications"
          />
        </div>
      </div>

      <div className="pt-2 flex justify-end">
        <Button
          type="button"
          onClick={handleSaveAll}
          disabled={isSaving}
          className="h-9 text-xs gap-2 min-w-[140px] bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs"
        >
          {isSaving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Check className="h-3.5 w-3.5" />
          )}
          <span>{isSaving ? "Saving..." : "Save Preferences"}</span>
        </Button>
      </div>
    </div>
  );
}
