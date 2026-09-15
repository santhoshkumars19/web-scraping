/**
 * types/websocket.ts
 *
 * Discriminated union types for WebSocket real-time progress events
 * broadcast by the FastAPI backend at WS /api/ws/tasks/{task_id}
 */

import type { ScrapingStage, ScrapingTaskStatus } from "./progress";

export interface TaskMetrics {
  results_discovered?: number;
  websites_found?: number;
  websites_crawled?: number;
  phones_found?: number;
  emails_found?: number;
  addresses_found?: number;
  duplicates_removed?: number;
  failed_websites?: number;
  verified_count?: number;
  high_confidence_count?: number;
  medium_confidence_count?: number;
  low_confidence_count?: number;
}

export interface TaskSnapshotData extends TaskMetrics {
  status: ScrapingTaskStatus;
  current_stage: ScrapingStage;
  progress: number;
  location?: string;
  keyword?: string;
  created_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  failure_reason?: string | null;
}

export interface TaskProgressData extends TaskMetrics {
  progress: number;
  current_stage?: ScrapingStage;
  stage?: ScrapingStage;
}

export interface TaskStageData {
  stage: ScrapingStage;
  progress?: number;
}

export interface TaskActivityData {
  id?: string;
  message: string;
  level?: "info" | "success" | "warning" | "error";
  timestamp?: string;
  stage?: ScrapingStage;
}

export interface TaskCompletedData extends TaskMetrics {
  status: "COMPLETED";
  progress: 100;
  completed_at?: string;
  duration?: number;
}

export interface TaskFailedData {
  status: "FAILED";
  failure_reason?: string;
  error?: string;
}

export interface TaskCancelledData {
  status: "CANCELLED";
  reason?: string;
}

export interface TaskErrorData {
  code: string;
  message: string;
}

// ── Discriminated Unions ───────────────────────────────────────────────────────

export interface TaskSnapshotEvent {
  type: "task.snapshot";
  task_id: string;
  timestamp: string;
  data: TaskSnapshotData;
}

export interface TaskQueuedEvent {
  type: "task.queued";
  task_id: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

export interface TaskStartedEvent {
  type: "task.started";
  task_id: string;
  timestamp: string;
  data?: { started_at?: string };
}

export interface TaskProgressEvent {
  type: "task.progress";
  task_id: string;
  timestamp: string;
  data: TaskProgressData;
}

export interface TaskStageEvent {
  type: "task.stage_changed";
  task_id: string;
  timestamp: string;
  data: TaskStageData;
}

export interface TaskActivityEvent {
  type: "task.activity";
  task_id: string;
  timestamp: string;
  data: TaskActivityData;
}

export interface TaskCompletedEvent {
  type: "task.completed";
  task_id: string;
  timestamp: string;
  data: TaskCompletedData;
}

export interface TaskFailedEvent {
  type: "task.failed";
  task_id: string;
  timestamp: string;
  data: TaskFailedData;
}

export interface TaskCancelledEvent {
  type: "task.cancelled";
  task_id: string;
  timestamp: string;
  data: TaskCancelledData;
}

export interface TaskErrorEvent {
  type: "task.error";
  task_id: string;
  timestamp: string;
  data: TaskErrorData;
}

export interface TaskPingEvent {
  type: "ping";
  task_id?: string;
  timestamp: string;
}

export interface TaskPongEvent {
  type: "pong";
  task_id?: string;
  timestamp: string;
}

export type WebSocketTaskEvent =
  | TaskSnapshotEvent
  | TaskQueuedEvent
  | TaskStartedEvent
  | TaskProgressEvent
  | TaskStageEvent
  | TaskActivityEvent
  | TaskCompletedEvent
  | TaskFailedEvent
  | TaskCancelledEvent
  | TaskErrorEvent
  | TaskPingEvent
  | TaskPongEvent;
