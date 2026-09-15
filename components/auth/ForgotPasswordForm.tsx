"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Mail, ArrowLeft, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { authApi } from "@/lib/api";

const forgotSchema = z.object({
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
});

type ForgotFormData = z.infer<typeof forgotSchema>;

export function ForgotPasswordForm() {
  const [submitted, setSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState("");
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotFormData>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (data: ForgotFormData) => {
    setServerError(null);
    try {
      await authApi.forgotPassword(data.email);
    } catch {
      // The backend always returns 200 to prevent enumeration,
      // so a real error here is a network issue — show generic message.
      setServerError("An unexpected error occurred. Please try again.");
      return;
    }
    setSubmittedEmail(data.email);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="text-center space-y-4 py-2">
        <div className="mx-auto w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center shadow-2xs">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-[#0E0E0E]">Check your email</h3>
          <p className="text-xs text-[#5C5A53] mt-1.5 leading-relaxed">
            If an account exists for{" "}
            <span className="font-mono font-medium text-[#0E0E0E]">
              {submittedEmail}
            </span>
            , we&apos;ve sent password reset instructions.
          </p>
        </div>

        <div className="pt-2 space-y-2">
          <Button asChild className="w-full h-10 text-xs font-semibold bg-[#BE0B31] hover:bg-[#A5082A] text-white rounded-xl shadow-xs">
            <Link href="/login">
              <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
              <span>Back to Sign In</span>
            </Link>
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setSubmitted(false)}
            className="w-full text-xs text-[#5C5A53] hover:text-[#0E0E0E] h-8"
          >
            Try another email
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 text-xs" noValidate>
      {serverError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2 text-xs">
          <span>{serverError}</span>
        </div>
      )}

      <div className="space-y-1.5">
        <label htmlFor="forgot-email" className="font-medium text-[#0E0E0E] text-xs block">
          Email address
        </label>
        <div className="relative">
          <Input
            id="forgot-email"
            type="email"
            placeholder="name@company.com"
            autoComplete="email"
            {...register("email")}
            className={`h-9 text-xs pl-9 ${
              errors.email ? "border-rose-500 focus-visible:ring-rose-500" : ""
            }`}
          />
          <Mail className="h-4 w-4 text-[#9E9B93] absolute left-3 top-1/2 -translate-y-1/2" />
        </div>
        {errors.email && (
          <p className="text-[11px] text-rose-600 font-medium">
            {errors.email.message}
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={isSubmitting}
        className="w-full h-10 text-xs font-semibold bg-[#BE0B31] hover:bg-[#A5082A] text-white mt-1 rounded-xl shadow-xs"
      >
        {isSubmitting ? (
          <span className="flex items-center gap-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Sending Link...</span>
          </span>
        ) : (
          <span>Send Reset Link</span>
        )}
      </Button>

      <div className="pt-2 text-center text-xs">
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 text-[#5C5A53] hover:text-[#0E0E0E] font-medium"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Sign In</span>
        </Link>
      </div>
    </form>
  );
}
