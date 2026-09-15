"use client";

import { useState, useRef } from "react";
import { Camera, Trash2, Check, Loader2, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export function ProfileSettings() {
  const { user, updateProfile } = useAuth();

  const [name, setName] = useState(user?.name || "Demo User");
  const [company, setCompany] = useState(user?.company || "LeadScout Demo");
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(user?.avatarUrl);
  const [isSaving, setIsSaving] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const initials = name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  // Handle local image file picker
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please select a valid image file.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      setAvatarUrl(dataUrl);
      toast.success("Photo preview updated.", {
        description: "Click Save Changes to persist your avatar.",
      });
    };
    reader.readAsDataURL(file);
  };

  const handleRemovePhoto = () => {
    setAvatarUrl(undefined);
    if (fileInputRef.current) fileInputRef.current.value = "";
    toast.info("Photo removed.");
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    await updateProfile({
      name: name.trim(),
      company: company.trim(),
      avatarUrl,
    });

    setIsSaving(false);
  };

  return (
    <div className="rounded-xl border border-border/80 bg-white p-6 shadow-2xs space-y-6">
      <div>
        <h2 className="text-base font-bold text-foreground">User Profile</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Manage your personal identity and organization information.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6 text-xs">
        {/* Avatar Section */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 pb-4 border-b border-border/70">
          <Avatar className="h-16 w-16 border border-border shadow-xs">
            {avatarUrl && <AvatarImage src={avatarUrl} alt={name} />}
            <AvatarFallback className="bg-primary text-white font-bold text-lg">
              {initials || "DU"}
            </AvatarFallback>
          </Avatar>

          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-foreground">Profile Photo</div>
            <div className="text-[11px] text-muted-foreground">
              Supports JPG, PNG or WebP under 2MB.
            </div>
            <div className="flex items-center gap-2 pt-1">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                className="hidden"
                id="avatar-file-input"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="h-8 text-xs gap-1.5 bg-white"
              >
                <Camera className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Change photo</span>
              </Button>

              {avatarUrl && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemovePhoto}
                  className="h-8 text-xs gap-1.5 text-destructive hover:bg-rose-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Remove</span>
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Input Fields Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Full Name */}
          <div className="space-y-1.5">
            <label htmlFor="profile-name" className="font-semibold text-foreground block">
              Full Name
            </label>
            <Input
              id="profile-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="h-9 text-xs"
              required
            />
          </div>

          {/* Email (Read Only) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label htmlFor="profile-email" className="font-semibold text-foreground block">
                Email Address
              </label>
              <span className="text-[10px] text-muted-foreground font-mono">
                Read-only
              </span>
            </div>
            <Input
              id="profile-email"
              type="email"
              value={user?.email || "demo@leadscout.app"}
              disabled
              className="h-9 text-xs bg-slate-50 text-muted-foreground cursor-not-allowed"
            />
          </div>

          {/* Company */}
          <div className="space-y-1.5">
            <label htmlFor="profile-company" className="font-semibold text-foreground block">
              Company
            </label>
            <Input
              id="profile-company"
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="h-9 text-xs"
            />
          </div>

          {/* Role */}
          <div className="space-y-1.5">
            <label htmlFor="profile-role" className="font-semibold text-foreground block">
              Account Role
            </label>
            <Input
              id="profile-role"
              type="text"
              value={user?.role === "ADMIN" ? "Administrator" : "Standard User"}
              disabled
              className="h-9 text-xs bg-slate-50 text-muted-foreground cursor-not-allowed font-medium"
            />
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-2 flex justify-end">
          <Button
            type="submit"
            disabled={isSaving || !name.trim()}
            className="h-9 text-xs gap-2 min-w-[120px] bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs"
          >
            {isSaving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Check className="h-3.5 w-3.5" />
            )}
            <span>{isSaving ? "Saving..." : "Save Changes"}</span>
          </Button>
        </div>
      </form>
    </div>
  );
}
