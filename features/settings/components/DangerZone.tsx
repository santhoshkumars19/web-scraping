"use client";

import { useState } from "react";
import { AlertTriangle, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useAuth } from "@/context/AuthContext";

export function DangerZone() {
  const { deleteAccount } = useAuth();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  const isConfirmed = confirmText.trim() === "DELETE";

  const handleDelete = async () => {
    if (!isConfirmed) return;
    setIsDeleting(true);
    await new Promise((res) => setTimeout(res, 500));
    setConfirmOpen(false);
    deleteAccount();
  };

  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50/40 p-6 shadow-2xs space-y-4">
      <div>
        <h3 className="text-sm font-bold text-rose-950">Danger Zone</h3>
        <p className="text-xs text-rose-800 mt-0.5">
          Irreversible actions that affect your workspace credentials.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-1">
        <div className="text-xs text-rose-900 leading-relaxed">
          <div className="font-semibold text-rose-950">Delete Account</div>
          <div className="text-[11px] text-rose-800/90">
            Permanently revoke session tokens and clear all user credentials on this browser.
          </div>
        </div>

        <Button
          type="button"
          variant="destructive"
          size="sm"
          onClick={() => {
            setConfirmText("");
            setConfirmOpen(true);
          }}
          className="h-8 text-xs gap-1.5 shrink-0 bg-rose-600 hover:bg-rose-700 text-white"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Delete Account</span>
        </Button>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-full bg-rose-100 text-rose-600">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle className="text-sm font-bold text-foreground">
                  Delete your account?
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                  This action cannot be undone.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="py-2 space-y-3 text-xs text-muted-foreground leading-relaxed">
            <p>
              To confirm deletion, please type{" "}
              <strong className="text-rose-600 font-mono">DELETE</strong> in the
              box below:
            </p>

            <Input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="Type DELETE to confirm"
              className="h-9 text-xs font-mono"
              autoFocus
            />
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
              variant="destructive"
              size="sm"
              disabled={!isConfirmed || isDeleting}
              onClick={handleDelete}
              className="text-xs gap-1.5"
            >
              {isDeleting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="h-3.5 w-3.5" />
              )}
              <span>Permanently Delete</span>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
