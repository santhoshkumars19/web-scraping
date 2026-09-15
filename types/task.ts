export type TaskHistoryStatus = "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface TaskItem {
  id: string; // e.g. "TASK-000124"
  keyword: string; // e.g. "CBSE Schools"
  location: string; // e.g. "Puducherry"
  searchRadius: string; // e.g. "25 km"
  maxResults: number;
  maxPagesPerSite: number;
  selectedFields?: string[];
  status: TaskHistoryStatus;
  progress: number; // 0–100
  currentStage?: string; // e.g. "Extracting contact information"
  resultsCount: number;
  verifiedCount: number;
  createdAt: string; // display string e.g. "Sep 10, 2026 10:42 AM"
  startedAt?: string;
  completedAt?: string;
  duration: string; // e.g. "2m 14s" or "Running..."
  failureReason?: string;
  createdBy?: string;
}

export interface TaskFilterState {
  search: string;
  status: TaskHistoryStatus[];
  locations: string[];
  dateRange: "all" | "today" | "7d" | "30d" | "90d" | "custom";
  hasResults: "all" | "has_results" | "no_results";
}

export type TaskSortField =
  | "createdAt"
  | "keyword"
  | "location"
  | "resultsCount"
  | "status"
  | "duration";

export type SortDirection = "asc" | "desc";
