"use client";

import Link from "next/link";
import { BrandLogo } from "@/components/shared/BrandLogo";

interface AuthLayoutProps {
  children: React.ReactNode;
  headline: string;
  subtitle: string;
}

export function AuthLayout({ children, headline, subtitle }: AuthLayoutProps) {
  return (
    <div className="min-h-screen w-full flex flex-col justify-center items-center bg-[#F4F3EA] px-4 py-12 sm:px-6 lg:px-8">
      {/* ── Brand Logo Header ── */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="flex justify-center mb-5">
          <BrandLogo
            variant="light"
            size="lg"
            className="transition-transform hover:scale-105"
          />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-[-0.035em] text-[#0E0E0E]">
          {headline}
        </h2>
        <p className="mt-1.5 text-xs text-[#5C5A53] max-w-sm mx-auto leading-relaxed">
          {subtitle}
        </p>
      </div>

      {/* ── Main Form Card ── */}
      <div className="w-full sm:max-w-[420px]">
        <div className="rounded-2xl border border-[#E3E0D5] bg-white p-6 sm:p-8 shadow-sm">
          {children}
        </div>

        {/* Footer Legal & Info */}
        <div className="mt-6 text-center text-[11px] text-[#5C5A53]/80 space-x-3">
          <span>&copy; {new Date().getFullYear()} LeadScout Platform</span>
          <span>•</span>
          <Link href="#" className="hover:underline">Privacy Policy</Link>
          <span>•</span>
          <Link href="#" className="hover:underline">Terms of Service</Link>
        </div>
      </div>
    </div>
  );
}
