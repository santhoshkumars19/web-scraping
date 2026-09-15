import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { DashboardView } from "@/features/dashboard/DashboardView";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Automated lead discovery, crawling, extraction, and verification metrics.",
};

export default function DashboardPage() {
  return (
    <PageContainer>
      <DashboardView />
    </PageContainer>
  );
}
