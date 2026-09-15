"use client";

import { useState } from "react";
import { Key, Copy, Eye, EyeOff, RefreshCw, AlertTriangle, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import type { ApiKeyInfo } from "@/types/auth";
import { loadApiKeyInfo, regenerateApiKey } from "@/lib/auth/mockAuth";

export function ApiAccessSettings() {
  const [apiKeyInfo, setApiKeyInfo] = useState<ApiKeyInfo>(() => loadApiKeyInfo());
  const [revealed, setRevealed] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(apiKeyInfo.key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("API key copied.", {
        description: "Saved to your clipboard.",
      });
    } catch {
      toast.error("Failed to copy API key.");
    }
  };

  const handleConfirmRegenerate = async () => {
    setIsRegenerating(true);
    await new Promise((res) => setTimeout(res, 400));
    const newKey = regenerateApiKey();
    setApiKeyInfo(newKey);
    setIsRegenerating(false);
    setConfirmOpen(false);
    setRevealed(true);
    toast.success("API key regenerated.", {
      description: "Previous keys have been revoked.",
    });
  };

  return (
    <div className="rounded-xl border border-border/80 bg-white p-6 shadow-2xs space-y-6">
      <div>
        <h2 className="text-base font-bold text-foreground">API Access</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Manage API credentials for programmatic access and webhook integrations.
        </p>
      </div>

      <div className="space-y-4 max-w-xl text-xs">
        {/* API Key Box */}
        <div className="space-y-1.5">
          <label className="font-semibold text-foreground block">
            Live Secret Key
          </label>
          <div className="flex items-center rounded-lg border border-border bg-slate-50 p-2 text-xs font-mono">
            <div className="flex-1 truncate select-all px-2 text-foreground font-medium">
              {revealed ? apiKeyInfo.key : apiKeyInfo.maskedKey}
            </div>

            <div className="flex items-center gap-1 shrink-0 pl-2 border-l border-border/70">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setRevealed(!revealed)}
                className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                title={revealed ? "Hide key" : "Reveal key"}
              >
                {revealed ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              </Button>

              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                title="Copy API key"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-emerald-600" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>
          </div>
          <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-0.5">
            <span>Created: {apiKeyInfo.createdAt}</span>
            <span>Last used: {apiKeyInfo.lastUsed}</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="pt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setConfirmOpen(true)}
            className="h-8 text-xs gap-1.5 text-rose-700 hover:text-rose-800 hover:bg-rose-50 border-rose-200"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Regenerate API Key</span>
          </Button>
        </div>

        {/* Integration Note */}
        <div className="p-3.5 rounded-lg border border-border/70 bg-slate-50 text-[11px] text-muted-foreground leading-relaxed">
          <span className="font-semibold text-foreground">Developer Tip: </span>
          Use this key in the Authorization header:{" "}
          <code className="bg-white px-1.5 py-0.5 rounded border border-border text-foreground font-mono text-[10px]">
            Bearer ls_live_...
          </code>
          . Never expose this secret in client-side code.
        </div>
      </div>

      {/* ── Regenerate Confirmation Dialog ── */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-full bg-amber-50 text-amber-600">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle className="text-sm font-bold text-foreground">
                  Regenerate API key?
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                  The current key will immediately stop working.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="py-2 text-xs text-muted-foreground leading-relaxed">
            Any scraping worker scripts, CRM connectors, or webhook automations
            using this API key will immediately lose access until updated.
          </div>

          <DialogFooter className="gap-2 sm:gap-0 mt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setConfirmOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={isRegenerating}
              onClick={handleConfirmRegenerate}
              className="text-xs bg-rose-600 hover:bg-rose-700 text-white"
            >
              {isRegenerating ? "Regenerating..." : "Regenerate Key"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
