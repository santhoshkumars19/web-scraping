import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { ScrapingProgressPage } from "@/features/progress/ScrapingProgressPage";

export const metadata: Metadata = {
  title: "Scraping Progress",
};

interface Props {
  params: Promise<{ taskId: string }>;
}

export default async function TaskProgressPage({ params }: Props) {
  const { taskId } = await params;

  return (
    <PageContainer>
      <ScrapingProgressPage taskId={taskId} />
    </PageContainer>
  );
}
