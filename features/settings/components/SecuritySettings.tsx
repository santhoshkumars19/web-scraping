"use client";

import { useState } from "react";
import { Lock, Eye, EyeOff, Loader2, Check, ShieldCheck, Laptop, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordStrength } from "@/components/auth/PasswordStrength";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export function SecuritySettings() {
  const { logout, changePassword } = useAuth();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [isChanging, setIsChanging] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!currentPassword) {
      toast.error("Enter your current password.");
      return;
    }

    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }

    setIsChanging(true);
    const result = await changePassword(currentPassword, newPassword);

    if (result.success) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } else {
      toast.error("Password change failed.", {
        description: result.error || "Please check your current password.",
      });
    }
    setIsChanging(false);
  };

  return (
    <div className="space-y-6">
      {/* ── Password Change Form ── */}
      <div className="rounded-xl border border-border/80 bg-white p-6 shadow-2xs space-y-6">
        <div>
          <h2 className="text-base font-bold text-foreground">Change Password</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Ensure your account is using a secure, long password.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 max-w-lg text-xs">
          {/* Current Password */}
          <div className="space-y-1.5">
            <label htmlFor="current-pass" className="font-semibold text-foreground block">
              Current Password
            </label>
            <Input
              id="current-pass"
              type={showPass ? "text" : "password"}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              className="h-9 text-xs"
              required
            />
          </div>

          {/* New Password */}
          <div className="space-y-1.5">
            <label htmlFor="new-pass" className="font-semibold text-foreground block">
              New Password
            </label>
            <div className="relative">
              <Input
                id="new-pass"
                type={showPass ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="h-9 text-xs pr-9"
                required
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-0.5"
                aria-label={showPass ? "Hide password" : "Show password"}
              >
                {showPass ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              </button>
            </div>
            <PasswordStrength password={newPassword} />
          </div>

          {/* Confirm New Password */}
          <div className="space-y-1.5">
            <label htmlFor="confirm-pass" className="font-semibold text-foreground block">
              Confirm New Password
            </label>
            <Input
              id="confirm-pass"
              type={showPass ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="h-9 text-xs"
              required
            />
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              disabled={isChanging || !newPassword || !currentPassword}
              className="h-9 text-xs gap-2 min-w-[140px] bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs"
            >
              {isChanging ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Check className="h-3.5 w-3.5" />
              )}
              <span>{isChanging ? "Changing..." : "Change Password"}</span>
            </Button>
          </div>
        </form>
      </div>

      {/* ── Active Sessions ── */}
      <div className="rounded-xl border border-border/80 bg-white p-6 shadow-2xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-foreground">Current Session</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Devices that are currently signed into your LeadScout workspace.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-border/60 bg-slate-50/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-white border border-border text-slate-700 shadow-2xs">
              <Laptop className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <span>Chrome on Windows</span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Active
                </span>
              </div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                Puducherry, India • Last active: Just now
              </div>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={logout}
            className="h-8 text-xs gap-1.5 bg-white text-muted-foreground hover:text-destructive hover:bg-rose-50"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Log Out</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
