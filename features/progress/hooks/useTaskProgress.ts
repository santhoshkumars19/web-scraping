"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  TaskProgress,
  ActivityEntry,
  WebsiteEntry,
  ScrapingStage,
  ScrapingTaskStatus,
} from "@/types/progress";
import {
  tasksApi,
  getWsUrl,
  API_ROUTES,
  getStoredToken,
  BackendTaskDetail,
  ApiError,
} from "@/lib/api";
import type { WebSocketTaskEvent } from "@/types/websocket";

interface UseTaskProgressReturn {
  task: TaskProgress | null;
  activityLog: ActivityEntry[];
  websites: WebsiteEntry[];
  notFound: boolean;
  isWsConnected: boolean;
  isReconnecting: boolean;
  cancelTask: () => void;
  retryTask: () => void;
  triggerFailure: () => void;
}

const MAX_RECONNECT_ATTEMPTS = 5;

function mapBackendDetailToTaskProgress(
  d: BackendTaskDetail,
  existing?: TaskProgress | null
): TaskProgress {
  return {
    taskId: d.task_id,
    status: (d.status?.toUpperCase() as ScrapingTaskStatus) || "PENDING",
    location: d.location || existing?.location || "",
    keyword: d.keyword || existing?.keyword || "",
    searchRadius: String(d.search_radius || existing?.searchRadius || 25),
    maxResults: d.max_results || existing?.maxResults || 100,
    maxPagesPerSite: d.max_pages_per_site || existing?.maxPagesPerSite || 20,
    progress: d.progress ?? existing?.progress ?? 0,
    currentStage: (d.current_stage as ScrapingStage) || existing?.currentStage || "CREATING_TASK",
    resultsDiscovered: d.results_discovered ?? existing?.resultsDiscovered ?? 0,
    websitesFound: d.websites_found ?? existing?.websitesFound ?? 0,
    websitesCrawled: d.websites_crawled ?? existing?.websitesCrawled ?? 0,
    phonesFound: d.phones_found ?? existing?.phonesFound ?? 0,
    emailsFound: d.emails_found ?? existing?.emailsFound ?? 0,
    addressesFound: d.addresses_found ?? existing?.addressesFound ?? 0,
    duplicatesRemoved: d.duplicates_removed ?? existing?.duplicatesRemoved ?? 0,
    failedWebsites: d.failed_websites ?? existing?.failedWebsites ?? 0,
    blockedWebsites: existing?.blockedWebsites ?? 0,
    timeoutWebsites: existing?.timeoutWebsites ?? 0,
    startedAt: d.started_at || d.created_at || existing?.startedAt || new Date().toISOString(),
    completedAt: d.completed_at || existing?.completedAt,
    failureReason: d.failure_reason || existing?.failureReason,
  };
}

export function useTaskProgress(taskId: string): UseTaskProgressReturn {
  const router = useRouter();
  const [notFound, setNotFound] = useState(false);
  const [task, setTask] = useState<TaskProgress | null>(null);
  const [activityLog, setActivityLog] = useState<ActivityEntry[]>([]);
  const [websites, setWebsites] = useState<WebsiteEntry[]>([]);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const activityIdsRef = useRef<Set<string>>(new Set());

  // ── Helper to append unique activity logs ──────────────────────────────────
  const appendActivity = useCallback((entry: ActivityEntry) => {
    if (activityIdsRef.current.has(entry.id)) return;
    activityIdsRef.current.add(entry.id);
    setActivityLog((prev) => [entry, ...prev]);
  }, []);

  // ── 1. Initial REST Hydration ──────────────────────────────────────────────
  const fetchTaskDetails = useCallback(async () => {
    if (!taskId || taskId.trim() === "" || taskId === "undefined") {
      setNotFound(true);
      return;
    }

    try {
      const res = await tasksApi.getTask(taskId);
      setTask((prev) => mapBackendDetailToTaskProgress(res.data, prev));
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
      } else {
        // Check sessionStorage fallback if freshly created
        try {
          const stored = sessionStorage.getItem(`task_${taskId}`);
          if (stored) {
            const parsed = JSON.parse(stored);
            setTask((prev) => ({
              taskId,
              status: "PENDING",
              location: parsed.location || "",
              keyword: parsed.keyword || "",
              searchRadius: String(parsed.searchRadius || 25),
              maxResults: Number(parsed.maxResults) || 100,
              maxPagesPerSite: Number(parsed.maxPagesPerSite) || 20,
              progress: 0,
              currentStage: "CREATING_TASK",
              resultsDiscovered: 0,
              websitesFound: 0,
              websitesCrawled: 0,
              phonesFound: 0,
              emailsFound: 0,
              addressesFound: 0,
              duplicatesRemoved: 0,
              failedWebsites: 0,
              blockedWebsites: 0,
              timeoutWebsites: 0,
              startedAt: parsed.createdAt || new Date().toISOString(),
              ...prev,
            }));
          }
        } catch {}
      }
    }
  }, [taskId]);

  useEffect(() => {
    fetchTaskDetails();
  }, [fetchTaskDetails]);

  // ── 2. WebSocket Connection Lifecycle ──────────────────────────────────────
  const connectWebSocket = useCallback(() => {
    if (!taskId || notFound) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const token = getStoredToken();
    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : "";
    const wsUrl = getWsUrl(`${API_ROUTES.wsTask(taskId)}${tokenQuery}`);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsWsConnected(true);
        setIsReconnecting(false);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const payload: WebSocketTaskEvent = JSON.parse(event.data);

          if (payload.type === "ping") {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "pong" }));
            }
            return;
          }

          if (payload.type === "task.snapshot") {
            const snap = payload.data;
            setTask((prev) => ({
              taskId: payload.task_id,
              status: (snap.status?.toUpperCase() as ScrapingTaskStatus) || prev?.status || "PENDING",
              location: snap.location || prev?.location || "",
              keyword: snap.keyword || prev?.keyword || "",
              searchRadius: prev?.searchRadius || "25",
              maxResults: prev?.maxResults || 100,
              maxPagesPerSite: prev?.maxPagesPerSite || 20,
              progress: snap.progress ?? prev?.progress ?? 0,
              currentStage: (snap.current_stage as ScrapingStage) || prev?.currentStage || "CREATING_TASK",
              resultsDiscovered: snap.results_discovered ?? prev?.resultsDiscovered ?? 0,
              websitesFound: snap.websites_found ?? prev?.websitesFound ?? 0,
              websitesCrawled: snap.websites_crawled ?? prev?.websitesCrawled ?? 0,
              phonesFound: snap.phones_found ?? prev?.phonesFound ?? 0,
              emailsFound: snap.emails_found ?? prev?.emailsFound ?? 0,
              addressesFound: snap.addresses_found ?? prev?.addressesFound ?? 0,
              duplicatesRemoved: snap.duplicates_removed ?? prev?.duplicatesRemoved ?? 0,
              failedWebsites: snap.failed_websites ?? prev?.failedWebsites ?? 0,
              blockedWebsites: prev?.blockedWebsites ?? 0,
              timeoutWebsites: prev?.timeoutWebsites ?? 0,
              startedAt: snap.started_at || snap.created_at || prev?.startedAt || new Date().toISOString(),
              completedAt: snap.completed_at || prev?.completedAt,
              failureReason: snap.failure_reason || prev?.failureReason,
            }));

            appendActivity({
              id: `snap-${payload.task_id}-${Date.now()}`,
              timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: `Connected to live pipeline (${snap.current_stage || "Initializing"})`,
              type: "info",
            });
          } else if (payload.type === "task.progress") {
            const p = payload.data;
            setTask((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                progress: p.progress ?? prev.progress,
                currentStage: (p.current_stage || p.stage || prev.currentStage) as ScrapingStage,
                resultsDiscovered: p.results_discovered ?? prev.resultsDiscovered,
                websitesFound: p.websites_found ?? prev.websitesFound,
                websitesCrawled: p.websites_crawled ?? prev.websitesCrawled,
                phonesFound: p.phones_found ?? prev.phonesFound,
                emailsFound: p.emails_found ?? prev.emailsFound,
                addressesFound: p.addresses_found ?? prev.addressesFound,
                duplicatesRemoved: p.duplicates_removed ?? prev.duplicatesRemoved,
                failedWebsites: p.failed_websites ?? prev.failedWebsites,
              };
            });
          } else if (payload.type === "task.stage_changed") {
            const st = payload.data;
            setTask((prev) => (prev ? {
              ...prev,
              currentStage: st.stage,
              progress: st.progress ?? prev.progress,
            } : null));

            appendActivity({
              id: `stage-${st.stage}-${Date.now()}`,
              timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: `Stage transitioned to ${st.stage}`,
              type: "info",
            });
          } else if (payload.type === "task.activity") {
            const act = payload.data;
            appendActivity({
              id: act.id || `act-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
              timestamp: act.timestamp || new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: act.message,
              type: act.level || "info",
            });
          } else if (payload.type === "task.completed") {
            const comp = payload.data;
            setTask((prev) => (prev ? {
              ...prev,
              status: "COMPLETED",
              progress: 100,
              currentStage: "COMPLETED",
              completedAt: comp.completed_at || new Date().toISOString(),
              resultsDiscovered: comp.results_discovered ?? prev.resultsDiscovered,
              websitesCrawled: comp.websites_crawled ?? prev.websitesCrawled,
              phonesFound: comp.phones_found ?? prev.phonesFound,
              emailsFound: comp.emails_found ?? prev.emailsFound,
            } : null));

            appendActivity({
              id: `comp-${Date.now()}`,
              timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: "Scraping pipeline finished successfully. All leads verified and ready.",
              type: "success",
            });
          } else if (payload.type === "task.failed") {
            const f = payload.data;
            setTask((prev) => (prev ? {
              ...prev,
              status: "FAILED",
              failureReason: f.failure_reason || f.error || "Scraping task encountered an error.",
            } : null));

            appendActivity({
              id: `fail-${Date.now()}`,
              timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: `Task failed: ${f.failure_reason || f.error || "Pipeline error"}`,
              type: "error",
            });
          } else if (payload.type === "task.cancelled") {
            setTask((prev) => (prev ? { ...prev, status: "CANCELLED" } : null));
            appendActivity({
              id: `canc-${Date.now()}`,
              timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: "Task was cancelled.",
              type: "warning",
            });
          }
        } catch {}
      };

      ws.onclose = () => {
        setIsWsConnected(false);
        wsRef.current = null;

        // Auto-reconnect with bounded backoff if task is still active
        setTask((currentTask) => {
          if (
            currentTask &&
            (currentTask.status === "RUNNING" || currentTask.status === "PENDING") &&
            reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS
          ) {
            setIsReconnecting(true);
            const delay = Math.min(16000, 1000 * Math.pow(2, reconnectAttemptsRef.current));
            reconnectAttemptsRef.current += 1;

            if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = setTimeout(() => {
              connectWebSocket();
            }, delay);
          } else {
            setIsReconnecting(false);
          }
          return currentTask;
        });
      };

      ws.onerror = () => {
        setIsWsConnected(false);
      };
    } catch {
      setIsWsConnected(false);
    }
  }, [taskId, notFound, appendActivity]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [connectWebSocket]);

  // ── 3. Fallback Polling when WebSocket is Disconnected ───────────────────────
  useEffect(() => {
    // Poll fast (every 2 seconds) whenever WS is not connected and task is active
    const isTaskActive = task && (task.status === "RUNNING" || task.status === "PENDING");

    if (!isWsConnected && isTaskActive) {
      const pollTask = async () => {
        try {
          const res = await tasksApi.getTask(taskId);
          const newDetail = res.data;
          setTask((prev) => {
            if (prev && newDetail.current_stage && newDetail.current_stage !== prev.currentStage) {
              appendActivity({
                id: `stage-${newDetail.current_stage}-${Date.now()}`,
                timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
                message: `Stage transitioned to ${newDetail.current_stage}`,
                type: "info",
              });
            }
            if (prev && newDetail.status === "COMPLETED" && prev.status !== "COMPLETED") {
              appendActivity({
                id: `comp-${Date.now()}`,
                timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
                message: "Scraping pipeline finished successfully. All leads verified and ready.",
                type: "success",
              });
            }
            if (prev && newDetail.status === "FAILED" && prev.status !== "FAILED") {
              appendActivity({
                id: `fail-${Date.now()}`,
                timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
                message: `Task failed: ${newDetail.failure_reason || "Pipeline error"}`,
                type: "error",
              });
            }
            return mapBackendDetailToTaskProgress(newDetail, prev);
          });
        } catch {}
      };

      pollTask();
      pollTimerRef.current = setInterval(pollTask, 2000);
    } else {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [isWsConnected, task?.status, taskId, appendActivity]);

  // ── 4. Actions ─────────────────────────────────────────────────────────────
  const cancelTask = useCallback(() => {
    toast.info("Task cancellation is handled automatically by the worker.", {
      description: "Any leads gathered so far will remain preserved.",
    });
  }, []);

  const retryTask = useCallback(() => {
    if (!task) return;
    router.push(
      `/tasks/new?keyword=${encodeURIComponent(task.keyword)}&location=${encodeURIComponent(
        task.location
      )}&radius=${task.searchRadius}&maxResults=${task.maxResults}`
    );
  }, [task, router]);

  const triggerFailure = useCallback(() => {
    // Development helper
    setTask((prev) => (prev ? { ...prev, status: "FAILED", failureReason: "Manually triggered failure state." } : null));
  }, []);

  return {
    task,
    activityLog,
    websites,
    notFound,
    isWsConnected,
    isReconnecting,
    cancelTask,
    retryTask,
    triggerFailure,
  };
}
