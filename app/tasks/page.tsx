import type { Metadata } from "next";
import { PageContainer } from "@/components/shared/PageContainer";
import { TasksPage } from "@/features/tasks/TasksPage";

export const metadata: Metadata = {
  title: "Task History",
  description: "View and manage your scraping tasks.",
};

export default function TasksRoute() {
  return (
    <PageContainer>
      <TasksPage />
    </PageContainer>
  );
}
