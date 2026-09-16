"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Plus, RefreshCw, Users, Globe, ShieldCheck, ListTodo } from "lucide-react";

import { PrimaryButton } from "@/components/shared/PrimaryButton";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/features/dashboard/MetricCard";
import { RecentTasksTable } from "@/features/dashboard/RecentTasksTable";
import { LeadOverview } from "@/features/dashboard/LeadOverview";
import { QuickActions } from "@/features/dashboard/QuickActions";
import { dashboardApi, DashboardSummaryData } from "@/lib/api";
import type { RecentTask, MetricData } from "@/mock/dashboard";

export function DashboardView() {
  const [data, setData] = useState<DashboardSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSummary = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const res = await dashboardApi.getSummary();
      setData(res.data);
    } catch (err) {
      console.error("Dashboard summary fetch failed:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const totalLeads = data?.total_leads ?? 0;
  const websitesDiscovered = data?.websites_discovered ?? 0;
  const verifiedLeads = data?.verified_leads ?? 0;
  const scrapingTasks = data?.scraping_tasks ?? 0;
  const verifiedRate = totalLeads > 0 ? Math.round((verifiedLeads / totalLeads) * 100) : 0;

  const metrics: MetricData[] = [
    {
      id: "total_leads",
      label: "Total Leads Discovered",
      value: totalLeads.toLocaleString(),
      rawValue: totalLeads,
      change: "+100%",
      changePositive: true,
      changeLabel: "Public sources",
    },
    {
      id: "websites_discovered",
      label: "Websites Crawled",
      value: websitesDiscovered.toLocaleString(),
      rawValue: websitesDiscovered,
      change: "Safe crawl",
      changePositive: true,
      changeLabel: "robots.txt verified",
    },
    {
      id: "verified_leads",
      label: "Verified Leads",
      value: verifiedLeads.toLocaleString(),
      rawValue: verifiedLeads,
      change: `${verifiedRate}%`,
      changePositive: true,
      changeLabel: "High/Medium confidence",
    },
    {
      id: "scraping_tasks",
      label: "Scraping Tasks",
      value: scrapingTasks.toLocaleString(),
      rawValue: scrapingTasks,
      change: "Active/done",
      changePositive: true,
      changeLabel: "Discovery runs",
    },
  ];

  const recentTasksMapped: RecentTask[] = (data?.recent_tasks || []).map((t) => ({
    taskId: t.task_id,
    keyword: t.keyword,
    location: t.location,
    results: t.results_count,
    status: (t.status?.toUpperCase() as RecentTask["status"]) || "PENDING",
    createdAt: new Date(t.created_at).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <div className="space-y-6">
      {/* ── Hero Banner ── */}
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between pb-2">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="h-1.5 w-1.5 rounded-[2px] bg-primary shrink-0" aria-hidden="true" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Automated Lead Discovery & Verification
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-[-0.035em] text-foreground font-sans leading-[1.15]">
            Smart Lead Scouting for Modern Growth
          </h1>
          <p className="mt-2.5 text-sm text-muted-foreground leading-relaxed max-w-xl">
            Discover organizations across any location, crawl verified domains, and extract verified contact information into your CRM pipeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchSummary(true)}
            disabled={loading || refreshing}
            className="rounded-xl px-4 h-10 font-medium text-xs bg-white"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="secondary"
            asChild
            className="rounded-xl px-5 h-10 font-medium"
          >
            <Link href="/leads">
              Browse Leads
            </Link>
          </Button>
          <PrimaryButton asChild className="h-10 px-4 sm:px-5">
            <Link href="/tasks/new">
              <Plus className="h-4 w-4 mr-1.5" />
              <span className="hidden sm:inline">New Scraping Task</span>
              <span className="sm:hidden">New Task</span>
            </Link>
          </PrimaryButton>
        </div>
      </div>

      {/* ── Metric Cards ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.id} metric={metric} />
        ))}
      </div>

      {/* ── Recent Activity Table ── */}
      <RecentTasksTable tasks={recentTasksMapped} loading={loading} />

      {/* ── Lead Overview Charts ── */}
      <LeadOverview
        categories={data?.category_summary}
        locations={data?.location_summary}
        loading={loading}
      />

      {/* ── Quick Actions ── */}
      <QuickActions />
    </div>
  );
}
