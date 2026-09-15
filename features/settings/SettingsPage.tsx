"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { User, Sliders, ShieldCheck, Key, Settings } from "lucide-react";
import { ProfileSettings } from "./components/ProfileSettings";
import { PreferenceSettings } from "./components/PreferenceSettings";
import { NotificationSettings } from "./components/NotificationSettings";
import { SecuritySettings } from "./components/SecuritySettings";
import { ApiAccessSettings } from "./components/ApiAccessSettings";
import { DangerZone } from "./components/DangerZone";

type SettingsTab = "profile" | "preferences" | "security" | "api";

const SETTINGS_TABS: { id: SettingsTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "preferences", label: "Preferences", icon: Sliders },
  { id: "security", label: "Security", icon: ShieldCheck },
  { id: "api", label: "API Access", icon: Key },
];

interface SettingsPageProps {
  defaultTab?: SettingsTab;
}

export function SettingsPage({ defaultTab }: SettingsPageProps = {}) {
  const searchParams = useSearchParams();
  const router = useRouter();

  const tabParam = searchParams.get("tab") as SettingsTab | null;
  const initialTab: SettingsTab =
    defaultTab && ["profile", "preferences", "security", "api"].includes(defaultTab)
      ? defaultTab
      : tabParam && ["profile", "preferences", "security", "api"].includes(tabParam)
      ? tabParam
      : "profile";

  const [activeTab, setActiveTab] = useState<SettingsTab>(initialTab);

  useEffect(() => {
    if (defaultTab && ["profile", "preferences", "security", "api"].includes(defaultTab)) {
      setActiveTab(defaultTab);
    } else if (tabParam && ["profile", "preferences", "security", "api"].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [defaultTab, tabParam]);

  const handleTabChange = (tab: SettingsTab) => {
    setActiveTab(tab);
    router.replace(`/settings/${tab}`);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* ── Page Header ── */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">
          Settings
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Manage your account credentials, workspace defaults, notifications, and API keys.
        </p>
      </div>

      {/* ── Mobile Horizontal Scroll Tabs ── */}
      <div className="flex md:hidden items-center gap-1.5 overflow-x-auto pb-1 border-b border-border/80">
        {SETTINGS_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? "bg-primary text-white"
                  : "text-muted-foreground hover:bg-slate-100"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ── Two-Column Layout (Desktop) ── */}
      <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-6 items-start">
        {/* Left Navigation Sidebar (Desktop) */}
        <div className="hidden md:flex flex-col gap-1 rounded-xl border border-border/80 bg-white p-2 shadow-2xs">
          {SETTINGS_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors text-left ${
                  isActive
                    ? "bg-primary/10 text-primary font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-slate-50"
                }`}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 ${
                    isActive ? "text-primary" : "text-muted-foreground"
                  }`}
                />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Right Content Area */}
        <div className="space-y-6 min-w-0">
          {activeTab === "profile" && <ProfileSettings />}

          {activeTab === "preferences" && (
            <div className="space-y-6">
              <PreferenceSettings />
              <NotificationSettings />
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              <SecuritySettings />
              <DangerZone />
            </div>
          )}

          {activeTab === "api" && <ApiAccessSettings />}
        </div>
      </div>
    </div>
  );
}
