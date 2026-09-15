import type { Metadata } from "next";
import { Suspense } from "react";
import { PageContainer } from "@/components/shared/PageContainer";
import { SettingsPage } from "@/features/settings/SettingsPage";

interface SettingsTabRouteProps {
  params: Promise<{ tab: string }>;
}

export async function generateMetadata({ params }: SettingsTabRouteProps): Promise<Metadata> {
  const { tab } = await params;
  const capitalized = tab.charAt(0).toUpperCase() + tab.slice(1);
  return {
    title: `${capitalized} Settings`,
    description: `Configure your LeadScout ${tab} settings.`,
  };
}

export default async function SettingsTabRoute({ params }: SettingsTabRouteProps) {
  const { tab } = await params;
  return (
    <PageContainer>
      <Suspense fallback={<div className="h-64 flex items-center justify-center text-xs text-muted-foreground">Loading settings...</div>}>
        <SettingsPage defaultTab={tab as any} />
      </Suspense>
    </PageContainer>
  );
}

