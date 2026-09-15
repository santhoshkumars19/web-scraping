"use client";

import {
  Search,
  Globe,
  Compass,
  Phone,
  Mail,
  MapPin,
  CopyX,
  AlertTriangle,
} from "lucide-react";
import type { TaskProgress } from "@/types/progress";

interface ProgressMetricsProps {
  task: TaskProgress;
}

export function ProgressMetrics({ task }: ProgressMetricsProps) {
  const metrics = [
    {
      label: "Results Discovered",
      value: task.resultsDiscovered.toLocaleString(),
      description: `Target: up to ${task.maxResults}`,
      icon: Search,
      color: "text-primary bg-primary/10",
    },
    {
      label: "Websites Found",
      value: task.websitesFound.toLocaleString(),
      description: "Official domains identified",
      icon: Globe,
      color: "text-foreground bg-muted",
    },
    {
      label: "Websites Crawled",
      value: `${task.websitesCrawled} / ${task.websitesFound}`,
      description: "Pages visited & parsed",
      icon: Compass,
      color: "text-primary bg-primary/10",
    },
    {
      label: "Phone Numbers Found",
      value: task.phonesFound.toLocaleString(),
      description: "Direct & landline contacts",
      icon: Phone,
      color: "text-emerald-700 bg-emerald-50",
    },
    {
      label: "Emails Found",
      value: task.emailsFound.toLocaleString(),
      description: "Public contact & office emails",
      icon: Mail,
      color: "text-amber-700 bg-amber-50",
    },
    {
      label: "Addresses Found",
      value: task.addressesFound.toLocaleString(),
      description: "Physical & postal locations",
      icon: MapPin,
      color: "text-emerald-700 bg-emerald-50",
    },
    {
      label: "Duplicates Removed",
      value: task.duplicatesRemoved.toLocaleString(),
      description: "Merged organization records",
      icon: CopyX,
      color: "text-muted-foreground bg-muted",
    },
    {
      label: "Failed Websites",
      value: task.failedWebsites.toLocaleString(),
      description: `${task.timeoutWebsites} timeout · ${task.blockedWebsites} blocked`,
      icon: AlertTriangle,
      color: task.failedWebsites > 0 ? "text-primary bg-primary/10" : "text-muted-foreground bg-muted",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((m) => {
        const Icon = m.icon;
        return (
          <div
            key={m.label}
            className="rounded-2xl border border-border bg-white p-4 shadow-sm flex flex-col justify-between hover:border-border/80 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-xs font-medium text-muted-foreground">{m.label}</span>
              <div className={`p-2 rounded-xl shrink-0 ${m.color}`}>
                <Icon className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight text-foreground">{m.value}</div>
              <p className="mt-0.5 text-xs text-muted-foreground">{m.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
