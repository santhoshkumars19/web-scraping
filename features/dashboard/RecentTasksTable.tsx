"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Eye, ArrowUpRight, MoreHorizontal, Download, Copy } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { RecentTask } from "@/mock/dashboard";

function TaskRow({ task }: { task: RecentTask }) {
  return (
    <tr className="group border-b border-border last:border-0 hover:bg-[#FAF9F5] transition-colors">
      {/* Task ID */}
      <td className="py-3 pl-4 pr-3 sm:pl-6">
        <Link
          href={`/tasks/${task.taskId}/progress`}
          className="font-mono text-xs font-semibold text-primary hover:underline"
        >
          {task.taskId}
        </Link>
      </td>

      {/* Search / Keyword */}
      <td className="px-3 py-3">
        <span className="text-sm font-medium text-foreground">{task.keyword}</span>
      </td>

      {/* Location */}
      <td className="hidden px-3 py-3 sm:table-cell">
        <span className="text-sm text-muted-foreground">{task.location}</span>
      </td>

      {/* Results */}
      <td className="hidden px-3 py-3 lg:table-cell">
        <span className="text-sm font-medium text-foreground">
          {task.results > 0 ? task.results.toLocaleString() : "—"}
        </span>
      </td>

      {/* Status */}
      <td className="px-3 py-3">
        <StatusBadge status={task.status} />
      </td>

      {/* Created */}
      <td className="hidden px-3 py-3 xl:table-cell">
        <span className="text-xs text-muted-foreground">{task.createdAt}</span>
      </td>

      {/* Actions */}
      <td className="py-3 pl-3 pr-4 sm:pr-6">
        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="sm" asChild className="h-7 gap-1.5 text-xs">
            <Link href={`/tasks/${task.taskId}/progress`}>
              <Eye className="h-3.5 w-3.5" />
              View
            </Link>
          </Button>
          <Button variant="ghost" size="sm" asChild className="h-7 gap-1.5 text-xs">
            <Link href={`/leads?task=${task.taskId}`}>
              <ArrowUpRight className="h-3.5 w-3.5" />
              Leads
            </Link>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreHorizontal className="h-3.5 w-3.5" />
                <span className="sr-only">More options</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link href={`/leads?task=${task.taskId}`}>
                  <Download className="h-3.5 w-3.5 mr-2" />
                  View & Export Leads
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link
                  href={`/tasks/new?keyword=${encodeURIComponent(
                    task.keyword
                  )}&location=${encodeURIComponent(task.location)}`}
                >
                  <Copy className="h-3.5 w-3.5 mr-2" />
                  Duplicate Task
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </td>
    </tr>
  );
}

interface RecentTasksTableProps {
  tasks?: RecentTask[];
  loading?: boolean;
}

export function RecentTasksTable({ tasks: propTasks, loading }: RecentTasksTableProps) {
  const [tasks, setTasks] = useState<RecentTask[]>(propTasks || []);

  useEffect(() => {
    if (propTasks !== undefined) {
      setTasks(propTasks);
    }
  }, [propTasks]);

  return (
    <div className="rounded-2xl border border-border bg-white shadow-sm">
      {/* Card header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-4 sm:px-6">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-[#0E0E0E]">
            Recent Scraping Activity
          </h2>
          <p className="mt-0.5 text-xs text-[#5C5A53]">
            Your latest scraping tasks and results
          </p>
        </div>
        <Button variant="outline" size="sm" asChild className="text-xs">
          <Link href="/tasks">View All</Link>
        </Button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="py-12 flex justify-center items-center gap-2 text-xs text-muted-foreground">
          <span className="h-4 w-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          Loading activity…
        </div>
      ) : tasks.length === 0 ? (
        <div className="py-12 text-center text-xs text-muted-foreground">
          No scraping tasks yet. Click{" "}
          <Link href="/tasks/new" className="text-primary font-medium hover:underline">
            New Scraping Task
          </Link>{" "}
          to begin discovering verified leads.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border bg-[#F8F7F0]">
                <th className="py-2.5 pl-4 pr-3 text-xs font-semibold text-muted-foreground sm:pl-6">
                  Task ID
                </th>
                <th className="px-3 py-2.5 text-xs font-semibold text-muted-foreground">
                  Search
                </th>
                <th className="hidden px-3 py-2.5 text-xs font-semibold text-muted-foreground sm:table-cell">
                  Location
                </th>
                <th className="hidden px-3 py-2.5 text-xs font-semibold text-muted-foreground lg:table-cell">
                  Results
                </th>
                <th className="px-3 py-2.5 text-xs font-semibold text-muted-foreground">
                  Status
                </th>
                <th className="hidden px-3 py-2.5 text-xs font-semibold text-muted-foreground xl:table-cell">
                  Created
                </th>
                <th className="py-2.5 pl-3 pr-4 text-right text-xs font-semibold text-muted-foreground sm:pr-6">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <TaskRow key={task.taskId} task={task} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
