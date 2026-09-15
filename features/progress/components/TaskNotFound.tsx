"use client";

import Link from "next/link";
import { SearchX, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function TaskNotFound() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-4">
      <div className="p-4 rounded-full bg-slate-100 text-slate-500 mb-4">
        <SearchX className="h-8 w-8" />
      </div>

      <h1 className="text-xl font-bold text-foreground">
        Task not found
      </h1>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm">
        We couldn&apos;t find the scraping task you&apos;re looking for. It may have been deleted or the task ID is invalid.
      </p>

      <div className="mt-6 flex gap-3">
        <Button asChild variant="outline" size="sm" className="gap-2">
          <Link href="/tasks">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Tasks</span>
          </Link>
        </Button>
        <Button asChild size="sm">
          <Link href="/tasks/new">
            <span>Create New Task</span>
          </Link>
        </Button>
      </div>
    </div>
  );
}
