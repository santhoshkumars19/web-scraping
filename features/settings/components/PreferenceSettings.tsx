"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Check, Loader2, Sliders, Moon, Sun, Laptop } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import type { UserPreferences } from "@/types/auth";
import { loadPreferences, savePreferences } from "@/lib/auth/mockAuth";

export function PreferenceSettings() {
  const { theme, setTheme } = useTheme();
  const [prefs, setPrefs] = useState<UserPreferences>(() => loadPreferences());
  const [isSaving, setIsSaving] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    await new Promise((res) => setTimeout(res, 350));

    savePreferences(prefs);
    setIsSaving(false);
    toast.success("Preferences saved.", {
      description: "Default workspace parameters have been updated.",
    });
  };

  const handleThemeSelect = (selectedTheme: "system" | "light" | "dark") => {
    setPrefs((p) => ({ ...p, theme: selectedTheme }));
    setTheme(selectedTheme);
  };

  const currentActiveTheme = mounted ? theme || prefs.theme : prefs.theme;

  return (
    <div className="rounded-xl border border-border/80 bg-white p-6 shadow-2xs space-y-6">
      <div>
        <h2 className="text-base font-bold text-foreground">Workspace Preferences</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Configure default search depths, scraping constraints, and export formats.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-5 text-xs">
        {/* Theme Preference */}
        <div className="space-y-2">
          <label className="font-semibold text-foreground block">
            Interface Theme
          </label>
          <div className="grid grid-cols-3 gap-2.5 max-w-md">
            {[
              { id: "system", label: "System", icon: Laptop },
              { id: "light", label: "Light", icon: Sun },
              { id: "dark", label: "Dark", icon: Moon },
            ].map((themeOpt) => {
              const Icon = themeOpt.icon;
              const isSelected = currentActiveTheme === themeOpt.id;
              return (
                <button
                  key={themeOpt.id}
                  type="button"
                  onClick={() => handleThemeSelect(themeOpt.id as "system" | "light" | "dark")}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-xs font-medium transition-all ${
                    isSelected
                      ? "border-primary bg-primary/10 text-primary ring-1 ring-primary/20 font-semibold"
                      : "border-border text-muted-foreground hover:bg-muted/50"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{themeOpt.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Form Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          {/* Language */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground block">
              Language
            </label>
            <Select
              value={prefs.language}
              onValueChange={(val) => setPrefs((p) => ({ ...p, language: val }))}
            >
              <SelectTrigger className="h-9 text-xs">
                <SelectValue placeholder="Language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="English">English (United States)</SelectItem>
                <SelectItem value="French">Français</SelectItem>
                <SelectItem value="Spanish">Español</SelectItem>
                <SelectItem value="Tamil">தமிழ் (Tamil)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Default Export Format */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground block">
              Default Export Format
            </label>
            <Select
              value={prefs.defaultExportFormat}
              onValueChange={(val) =>
                setPrefs((p) => ({ ...p, defaultExportFormat: val as "csv" | "excel" }))
              }
            >
              <SelectTrigger className="h-9 text-xs">
                <SelectValue placeholder="Export Format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV Spreadsheet (.csv)</SelectItem>
                <SelectItem value="excel">Excel Workbook (.xlsx)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Default Location */}
          <div className="space-y-1.5">
            <label htmlFor="pref-location" className="font-semibold text-foreground block">
              Default Search Location
            </label>
            <Input
              id="pref-location"
              type="text"
              value={prefs.defaultLocation}
              onChange={(e) =>
                setPrefs((p) => ({ ...p, defaultLocation: e.target.value }))
              }
              className="h-9 text-xs"
            />
          </div>

          {/* Default Search Radius */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground block">
              Default Search Radius
            </label>
            <Select
              value={String(prefs.defaultSearchRadius)}
              onValueChange={(val) =>
                setPrefs((p) => ({ ...p, defaultSearchRadius: Number(val) }))
              }
            >
              <SelectTrigger className="h-9 text-xs">
                <SelectValue placeholder="Radius" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10 km (City center)</SelectItem>
                <SelectItem value="25">25 km (Standard metro)</SelectItem>
                <SelectItem value="50">50 km (Greater region)</SelectItem>
                <SelectItem value="100">100 km (Wide area)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Default Max Results */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground block">
              Default Maximum Results
            </label>
            <Select
              value={String(prefs.defaultMaxResults)}
              onValueChange={(val) =>
                setPrefs((p) => ({ ...p, defaultMaxResults: Number(val) }))
              }
            >
              <SelectTrigger className="h-9 text-xs">
                <SelectValue placeholder="Max Results" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="25">25 leads (Quick scan)</SelectItem>
                <SelectItem value="50">50 leads</SelectItem>
                <SelectItem value="100">100 leads (Standard)</SelectItem>
                <SelectItem value="250">250 leads (Deep discovery)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Default Pages Per Website */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground block">
              Default Pages Per Website
            </label>
            <Select
              value={String(prefs.defaultPagesPerWebsite)}
              onValueChange={(val) =>
                setPrefs((p) => ({ ...p, defaultPagesPerWebsite: Number(val) }))
              }
            >
              <SelectTrigger className="h-9 text-xs">
                <SelectValue placeholder="Pages per site" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5 pages (Shallow)</SelectItem>
                <SelectItem value="10">10 pages (Standard)</SelectItem>
                <SelectItem value="20">20 pages (Thorough)</SelectItem>
                <SelectItem value="50">50 pages (Exhaustive)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-2 flex justify-end">
          <Button
            type="submit"
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
      </form>
    </div>
  );
}
