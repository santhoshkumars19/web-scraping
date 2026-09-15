import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { LeadProfilePage } from "@/features/lead-details/LeadProfilePage";

export const metadata: Metadata = {
  title: "Lead Profile",
  description: "View comprehensive contact, verification, and source details for this discovered lead.",
};

interface LeadDetailsRouteProps {
  params: Promise<{ leadId: string }>;
}

export default async function LeadDetailsRoute({ params }: LeadDetailsRouteProps) {
  const { leadId } = await params;

  return (
    <PageContainer>
      <LeadProfilePage leadId={leadId} />
    </PageContainer>
  );
}
