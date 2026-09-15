import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";

export const metadata: Metadata = {
  title: "Reset Password",
  description: "Set a new password for your LeadScout account.",
};

export default function ResetPasswordPage() {
  return (
    <AuthLayout
      headline="Reset your password"
      subtitle="Enter a secure new password for your LeadScout account."
    >
      <Suspense fallback={<div className="h-32 flex items-center justify-center text-xs text-muted-foreground">Loading...</div>}>
        <ResetPasswordForm />
      </Suspense>
    </AuthLayout>
  );
}
