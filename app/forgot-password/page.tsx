import type { Metadata } from "next";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";

export const metadata: Metadata = {
  title: "Forgot Password",
  description: "Reset your LeadScout account password.",
};

export default function ForgotPasswordPage() {
  return (
    <AuthLayout
      headline="Forgot your password?"
      subtitle="Enter your email address and we'll help you reset your password."
    >
      <ForgotPasswordForm />
    </AuthLayout>
  );
}
