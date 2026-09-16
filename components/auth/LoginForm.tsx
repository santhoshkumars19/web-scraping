"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuth } from "@/context/AuthContext";

const REMEMBER_EMAIL_KEY = "leadscout_remember_email";

const loginSchema = z.object({
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
  password: z.string().min(1, "Password is required.").min(8, "Password must be at least 8 characters."),
  rememberMe: z.boolean(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect") || "/dashboard";

  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // Check remembered email
  const initialEmail =
    typeof window !== "undefined"
      ? localStorage.getItem(REMEMBER_EMAIL_KEY) || ""
      : "";

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: initialEmail,
      password: "",
      rememberMe: Boolean(initialEmail),
    },
  });

  const rememberMeValue = watch("rememberMe");

  const onSubmit = async (data: LoginFormData) => {
    setAuthError(null);
    const result = await login(data.email, data.password, data.rememberMe);

    if (result.success) {
      router.push(redirectUrl);
    } else {
      setAuthError(result.error || "Invalid email or password.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 text-xs" noValidate>
      {/* Inline Auth Error */}
      {authError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{authError}</span>
        </div>
      )}

      {/* Email Field */}
      <div className="space-y-1.5">
        <label
          htmlFor="email"
          className="font-medium text-[#0E0E0E] text-xs block"
        >
          Email address
        </label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="name@company.com"
          {...register("email")}
          className={`h-9 text-xs ${
            errors.email ? "border-rose-500 focus-visible:ring-rose-500" : ""
          }`}
        />
        {errors.email && (
          <p className="text-[11px] text-rose-600 font-medium">
            {errors.email.message}
          </p>
        )}
      </div>

      {/* Password Field */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor="password"
            className="font-medium text-[#0E0E0E] text-xs block"
          >
            Password
          </label>
          <Link
            href="/forgot-password"
            className="text-[11px] text-[#BE0B31] hover:underline font-medium"
          >
            Forgot password?
          </Link>
        </div>

        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
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
            {showPassword ? (
              <EyeOff className="h-3.5 w-3.5" />
            ) : (
              <Eye className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
        {errors.password && (
          <p className="text-[11px] text-rose-600 font-medium">
            {errors.password.message}
          </p>
        )}
      </div>

      {/* Remember Me */}
      <div className="flex items-center gap-2 pt-0.5">
        <Checkbox
          id="rememberMe"
          checked={rememberMeValue}
          onCheckedChange={(val) => setValue("rememberMe", Boolean(val))}
          className="h-3.5 w-3.5"
        />
        <label
          htmlFor="rememberMe"
          className="text-xs text-[#5C5A53] select-none cursor-pointer font-normal"
        >
          Remember me
        </label>
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        disabled={isSubmitting}
        className="w-full h-10 text-xs font-semibold bg-[#BE0B31] hover:bg-[#A5082A] text-white mt-2 rounded-xl shadow-xs"
      >
        {isSubmitting ? (
          <span className="flex items-center gap-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Signing in...</span>
          </span>
        ) : (
          <span>Sign In</span>
        )}
      </Button>

      {/* Bottom Link */}
      <div className="pt-2 text-center text-xs text-[#5C5A53]">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-[#BE0B31] hover:underline font-semibold">
          Create an account
        </Link>
      </div>
    </form>
  );
}
