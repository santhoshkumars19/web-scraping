import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { LeadsPage } from "@/features/leads/LeadsPage";

export const metadata: Metadata = {
  title: "Leads",
  description: "Manage, review, and organize your discovered organizations.",
};

interface LeadsPageRouteProps {
  searchParams: Promise<{ task?: string }>;
}

export default async function LeadsRoute({ searchParams }: LeadsPageRouteProps) {
  const { task } = await searchParams;

  return (
    <PageContainer>
      <LeadsPage initialTaskId={task} />
    </PageContainer>
  );
}
