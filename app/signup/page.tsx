import type { Metadata } from "next";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { SignupForm } from "@/components/auth/SignupForm";

export const metadata: Metadata = {
  title: "Create Account",
  description: "Create your LeadScout account.",
};

export default function SignupPage() {
  return (
    <AuthLayout
      headline="Create your LeadScout account"
      subtitle="Start discovering and managing leads."
    >
      <SignupForm />
    </AuthLayout>
  );
}
