"use client";

import { MapPin, Tag, Compass, Hash, FileText, Clock } from "lucide-react";
import type { TaskProgress } from "@/types/progress";

interface TaskSearchDetailsProps {
  task: TaskProgress;
}

export function TaskSearchDetails({ task }: TaskSearchDetailsProps) {
  const startedTime = new Date(task.startedAt).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  const details = [
    { label: "Location", value: task.location, icon: MapPin },
    { label: "Keyword", value: task.keyword, icon: Tag },
    { label: "Search Radius", value: `${task.searchRadius} km`, icon: Compass },
    { label: "Maximum Results", value: task.maxResults.toString(), icon: Hash },
    { label: "Pages / Website", value: task.maxPagesPerSite.toString(), icon: FileText },
    { label: "Started", value: startedTime, icon: Clock },
  ];

  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        Search Details
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {details.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex flex-col gap-1">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span>{item.label}</span>
              </div>
              <span className="text-sm font-semibold text-foreground truncate" title={item.value}>
                {item.value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
