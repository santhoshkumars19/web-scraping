import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { LoginForm } from "@/components/auth/LoginForm";

export const metadata: Metadata = {
  title: "Sign In",
  description: "Sign in to your LeadScout workspace.",
};

export default function LoginPage() {
  return (
    <AuthLayout
      headline="Welcome back"
      subtitle="Sign in to continue to your lead discovery workspace."
    >
      <Suspense fallback={<div className="h-64 flex items-center justify-center text-xs text-muted-foreground">Loading form...</div>}>
        <LoginForm />
      </Suspense>
    </AuthLayout>
  );
}
