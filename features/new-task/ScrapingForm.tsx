"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, FormProvider, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Radar, Save, X, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import {
  scrapingTaskSchema,
  DEFAULT_FORM_VALUES,
  saveDraft,
} from "@/types/task-form";
import type { ScrapingTaskFormData } from "@/types/task-form";
import { tasksApi, ApiError } from "@/lib/api";

import { DiscoverySection } from "./components/DiscoverySection";
import { LimitSection } from "./components/LimitSection";
import { DataFieldSelector } from "./components/DataFieldSelector";
import { AdvancedOptions } from "./components/AdvancedOptions";
import { ResponsibleCrawlingCard } from "./components/ResponsibleCrawlingCard";
import { TaskSummary } from "./components/TaskSummary";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ScrapingForm() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const methods = useForm<ScrapingTaskFormData>({
    resolver: zodResolver(scrapingTaskSchema) as any, // eslint-disable-line @typescript-eslint/no-explicit-any
    defaultValues: DEFAULT_FORM_VALUES,
    mode: "onBlur",
  });

  const { handleSubmit } = methods;

  // ── Submit ────────────────────────────────────────────────────────────────

  const onSubmit: SubmitHandler<ScrapingTaskFormData> = async (data) => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      const idempotencyKey = typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random()}`;

      const payload = {
        location: data.location.trim(),
        keyword: data.keyword.trim(),
        search_radius: Number(data.searchRadius) || 25,
        max_results: Number(data.maxResults) || 100,
        max_pages_per_site: Number(data.maxPagesPerSite) || 20,
        selected_fields: data.selectedFields,
        crawl_depth: Number(data.crawlDepth) || 3,
        follow_internal_links: Boolean(data.followInternalLinks),
        prioritize_contact: Boolean(data.prioritizeContact),
        prioritize_about: Boolean(data.prioritizeAbout),
        prioritize_admissions: Boolean(data.prioritizeAdmissions),
        prioritize_staff_management: Boolean(data.prioritizeStaffManagement),
      };

      const res = await tasksApi.createTask(payload, idempotencyKey);
      const taskId = res.data.task_id;

      // Store submitted task parameters in sessionStorage for instant hydration
      try {
        sessionStorage.setItem(
          `task_${taskId}`,
          JSON.stringify({
            ...data,
            taskId,
            status: "PENDING",
            createdAt: res.data.created_at || new Date().toISOString(),
          })
        );
      } catch {}

      toast.success("Scraping task created.", {
        description: `Task ID: ${taskId}`,
      });

      router.push(`/tasks/${taskId}/progress`);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 422) {
          const details = err.details as Record<string, string> | undefined;
          let description = err.message || "Request validation failed.";

          if (details && typeof details === "object" && !Array.isArray(details)) {
            const fieldMapping: Record<string, keyof ScrapingTaskFormData> = {
              location: "location",
              keyword: "keyword",
              search_radius: "searchRadius",
              max_results: "maxResults",
              max_pages_per_site: "maxPagesPerSite",
              selected_fields: "selectedFields",
              crawl_depth: "crawlDepth",
            };

            const messages: string[] = [];
            for (const [field, msg] of Object.entries(details)) {
              messages.push(msg);
              const formField = fieldMapping[field] || (field as keyof ScrapingTaskFormData);
              try {
                methods.setError(formField as any, { type: "server", message: msg });
              } catch {}
            }

            if (messages.length > 0) {
              description = messages.join(". ");
            }
          }

          toast.error("Please check the highlighted fields.", {
            description,
          });
        } else if (err.status === 429) {
          toast.error("Too many scraping requests. Please try again later.");
        } else if (err.status === 500 || err.status === 503) {
          toast.error("LeadScout is temporarily unavailable. Please try again.");
        } else {
          toast.error(err.message || "Failed to create task.");
        }
      } else {
        toast.error("Network error. Please verify your connection.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Save Draft ────────────────────────────────────────────────────────────

  function handleSaveDraft() {
    const values = methods.getValues();
    saveDraft(values);
    toast.success("Task draft saved.", {
      description: "Your configuration has been saved locally.",
    });
  }

  // ── Cancel ────────────────────────────────────────────────────────────────

  function handleCancel() {
    router.push("/dashboard");
  }

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        {/* ── Two-column layout ── */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">

          {/* ── LEFT: Form sections ── */}
          <div className="flex flex-col gap-5">
            <DiscoverySection />
            <LimitSection />
            <DataFieldSelector />
            <AdvancedOptions />
            <ResponsibleCrawlingCard />

            {/* ── Mobile: Task Summary here ── */}
            <div className="lg:hidden">
              <TaskSummary />
            </div>

            {/* ── Action buttons ── */}
            <div className="rounded-xl border border-border bg-card text-card-foreground p-5 shadow-sm">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                {/* Left: Cancel */}
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleCancel}
                  className="order-last sm:order-first w-full sm:w-auto gap-2 text-muted-foreground"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Cancel
                </Button>

                {/* Right: Save Draft + Start */}
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleSaveDraft}
                    className="w-full sm:w-auto gap-2"
                  >
                    <Save className="h-4 w-4" />
                    Save as Draft
                  </Button>

                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className={cn(
                      "w-full sm:w-auto gap-2 bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs",
                      "disabled:opacity-70"
                    )}
                  >
                    {isSubmitting ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Creating task…
                      </>
                    ) : (
                      <>
                        <Radar className="h-4 w-4" />
                        Start Scraping
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Sticky summary (desktop only) ── */}
          <div className="hidden lg:block">
            <TaskSummary />
          </div>
        </div>
      </form>
    </FormProvider>
  );
}
