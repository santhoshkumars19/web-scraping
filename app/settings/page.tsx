import type { Metadata } from "next";
import { Suspense } from "react";
import { PageContainer } from "@/components/shared/PageContainer";
import { SettingsPage } from "@/features/settings/SettingsPage";

export const metadata: Metadata = {
  title: "Settings",
  description: "Configure your LeadScout workspace, account credentials, and preferences.",
};

export default function SettingsRoute() {
  return (
    <PageContainer>
      <Suspense fallback={<div className="h-64 flex items-center justify-center text-xs text-muted-foreground">Loading settings...</div>}>
        <SettingsPage />
      </Suspense>
    </PageContainer>
  );
}
