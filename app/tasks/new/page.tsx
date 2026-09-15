import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { ScrapingForm } from "@/features/new-task/ScrapingForm";

export const metadata: Metadata = {
  title: "Create Scraping Task",
};

export default function NewTaskPage() {
  return (
    <PageContainer>
      <SectionHeader
        title="Create Scraping Task"
        description="Tell us where to search and what you're looking for."
        className="mb-6"
      />
      <ScrapingForm />
    </PageContainer>
  );
}
