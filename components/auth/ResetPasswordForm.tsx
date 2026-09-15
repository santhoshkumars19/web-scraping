"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordStrength } from "./PasswordStrength";
import { authApi } from "@/lib/api";

const resetSchema = z
  .object({
    password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .regex(/[A-Z]/, "Include at least one uppercase letter.")
      .regex(/[a-z]/, "Include at least one lowercase letter.")
      .regex(/[0-9]/, "Include at least one number."),
    confirmPassword: z.string().min(1, "Confirm your password."),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

type ResetFormData = z.infer<typeof resetSchema>;

export function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const resetToken = searchParams.get("token") ?? "";

  const [submitted, setSubmitted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResetFormData>({
    resolver: zodResolver(resetSchema),
  });

  const passwordValue = watch("password");

  const onSubmit = async (data: ResetFormData) => {
    setServerError(null);

    if (!resetToken) {
      setServerError("Missing or invalid reset token. Please request a new reset link.");
      return;
    }

    try {
      await authApi.resetPassword(resetToken, data.password);
      setSubmitted(true);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to reset password. The link may have expired.";
      setServerError(message);
    }
  };

  if (submitted) {
    return (
      <div className="text-center space-y-4 py-2">
        <div className="mx-auto w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center shadow-2xs">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-[#0E0E0E]">Password updated successfully</h3>
          <p className="text-xs text-[#5C5A53] mt-1.5 leading-relaxed">
            Your password has been changed. You can now sign in with your new credentials.
          </p>
        </div>

        <div className="pt-2">
          <Button asChild className="w-full h-10 text-xs font-semibold bg-[#BE0B31] hover:bg-[#A5082A] text-white rounded-xl shadow-xs">
            <Link href="/login">
              Continue to Sign In
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 text-xs" noValidate>
      {/* Server / token error */}
      {serverError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{serverError}</span>
        </div>
      )}

      {/* Missing token warning */}
      {!resetToken && (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
          No reset token found in the URL. Please request a new password reset link.
        </div>
      )}

      {/* New Password */}
      <div className="space-y-1.5">
        <label htmlFor="reset-password" className="font-medium text-[#0E0E0E] text-xs block">
          New password
        </label>
        <div className="relative">
          <Input
            id="reset-password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            placeholder="••••••••"
            {...register("password")}
            className={`h-9 text-xs pr-9 ${
              errors.password ? "border-rose-500 focus-visible:ring-rose-500" : ""
            }`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#5C5A53] hover:text-[#0E0E0E] p-0.5 cursor-pointer"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
          </button>
        </div>
        {errors.password && (
          <p className="text-[11px] text-rose-600 font-medium">
            {errors.password.message}
          </p>
        )}
        <PasswordStrength password={passwordValue} />
      </div>

      {/* Confirm Password */}
      <div className="space-y-1.5">
        <label htmlFor="reset-confirmPassword" className="font-medium text-[#0E0E0E] text-xs block">
          Confirm new password
        </label>
        <Input
          id="reset-confirmPassword"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••"
          {...register("confirmPassword")}
          className={`h-9 text-xs ${
            errors.confirmPassword ? "border-rose-500 focus-visible:ring-rose-500" : ""
          }`}
        />
        {errors.confirmPassword && (
          <p className="text-[11px] text-rose-600 font-medium">
            {errors.confirmPassword.message}
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={isSubmitting || !resetToken}
        className="w-full h-10 text-xs font-semibold bg-[#BE0B31] hover:bg-[#A5082A] text-white mt-2 rounded-xl shadow-xs"
      >
        {isSubmitting ? (
          <span className="flex items-center gap-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Updating Password...</span>
          </span>
        ) : (
          <span>Reset Password</span>
        )}
      </Button>

      <div className="pt-1 text-center text-xs">
        <Link href="/login" className="text-[#5C5A53] hover:text-[#0E0E0E] font-medium">
          Cancel and return to Sign In
        </Link>
      </div>
    </form>
  );
}
