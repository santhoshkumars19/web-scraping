import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { ExportsPage } from "@/features/exports/ExportsPage";

export const metadata: Metadata = {
  title: "Exports",
  description: "View and manage your exported lead files.",
};

export default function ExportsRoute() {
  return (
    <PageContainer>
      <ExportsPage />
    </PageContainer>
  );
}
