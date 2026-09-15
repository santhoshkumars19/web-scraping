"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { PasswordStrength } from "./PasswordStrength";
import { useAuth } from "@/context/AuthContext";

const signupSchema = z
  .object({
    name: z.string().min(2, "Full name is required."),
    email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .regex(/[A-Z]/, "Include at least one uppercase letter.")
      .regex(/[a-z]/, "Include at least one lowercase letter.")
      .regex(/[0-9]/, "Include at least one number."),
    confirmPassword: z.string().min(1, "Confirm your password."),
    terms: z.boolean().refine((val) => val === true, {
      message: "You must agree to the Terms and Privacy Policy.",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

type SignupFormData = z.infer<typeof signupSchema>;

export function SignupForm() {
  const router = useRouter();
  const { signup } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [signupError, setSignupError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      terms: false,
    },
  });

  const passwordValue = watch("password");
  const termsValue = watch("terms");

  const onSubmit = async (data: SignupFormData) => {
    setSignupError(null);
    const result = await signup(data.name, data.email, data.password);

    if (result.success) {
      router.push("/dashboard");
    } else {
      setSignupError(result.error || "Failed to create account.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5 text-xs" noValidate>
      {/* Inline Signup Error */}
      {signupError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{signupError}</span>
        </div>
      )}

      {/* Full Name */}
      <div className="space-y-1.5">
        <label htmlFor="name" className="font-medium text-[#0E0E0E] text-xs block">
          Full name
        </label>
        <Input
          id="name"
          type="text"
          placeholder="Jane Doe"
          autoComplete="name"
          {...register("name")}
          className={`h-9 text-xs ${
            errors.name ? "border-rose-500 focus-visible:ring-rose-500" : ""
          }`}
        />
        {errors.name && (
          <p className="text-[11px] text-rose-600 font-medium">
            {errors.name.message}
          </p>
        )}
      </div>

      {/* Email */}
      <div className="space-y-1.5">
        <label htmlFor="signup-email" className="font-medium text-[#0E0E0E] text-xs block">
          Work email
        </label>
        <Input
          id="signup-email"
          type="email"
          placeholder="name@company.com"
          autoComplete="email"
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

      {/* Password */}
      <div className="space-y-1.5">
        <label htmlFor="signup-password" className="font-medium text-[#0E0E0E] text-xs block">
          Password
        </label>
        <div className="relative">
          <Input
            id="signup-password"
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
        <label htmlFor="confirmPassword" className="font-medium text-[#0E0E0E] text-xs block">
          Confirm password
        </label>
        <Input
          id="confirmPassword"
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

      {/* Terms Checkbox */}
      <div className="space-y-1 pt-1">
        <div className="flex items-start gap-2">
          <Checkbox
            id="terms"
            checked={termsValue}
            onCheckedChange={(val) => setValue("terms", Boolean(val), { shouldValidate: true })}
            className="h-3.5 w-3.5 mt-0.5"
          />
          <label htmlFor="terms" className="text-[11px] text-[#5C5A53] select-none cursor-pointer leading-tight">
            I agree to the{" "}
            <Link href="#" className="text-[#BE0B31] hover:underline">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="#" className="text-[#BE0B31] hover:underline">
              Privacy Policy
            </Link>
            .
          </label>
        </div>
        {errors.terms && (
          <p className="text-[11px] text-rose-600 font-medium pl-5">
            {errors.terms.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        disabled={isSubmitting}
        className="w-full h-10 text-xs font-semibold bg-[#BE0B31] hover:bg-[#A5082A] text-white mt-3 rounded-xl shadow-xs"
      >
        {isSubmitting ? (
          <span className="flex items-center gap-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Creating Account...</span>
          </span>
        ) : (
          <span>Create Account</span>
        )}
      </Button>

      {/* Link to Login */}
      <div className="pt-2 text-center text-xs text-[#5C5A53]">
        Already have an account?{" "}
        <Link href="/login" className="text-[#BE0B31] hover:underline font-semibold">
          Sign in
        </Link>
      </div>
    </form>
  );
}
