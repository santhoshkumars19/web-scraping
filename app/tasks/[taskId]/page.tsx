import { redirect } from "next/navigation";

interface TaskPageProps {
  params: Promise<{ taskId: string }>;
}

export default async function TaskDetailPage({ params }: TaskPageProps) {
  const { taskId } = await params;
  redirect(`/tasks/${taskId}/progress`);
}

