// ─── Status & Stage Enums ────────────────────────────────────────────────────

export type ScrapingTaskStatus =
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "PENDING";

export type ScrapingStage =
  | "CREATING_TASK"
  | "DISCOVERING"
  | "FINDING_WEBSITES"
  | "CRAWLING"
  | "EXTRACTING"
  | "CLEANING"
  | "DEDUPLICATING"
  | "VERIFYING"
  | "SAVING"
  | "COMPLETED";

// ─── Stage metadata ──────────────────────────────────────────────────────────

export interface StageInfo {
  id: ScrapingStage;
  label: string;
  description: string;
  order: number;
}

export const STAGES: StageInfo[] = [
  { id: "CREATING_TASK",    label: "Creating task",                  description: "Setting up the scraping configuration",        order: 1 },
  { id: "DISCOVERING",      label: "Discovering organizations",       description: "Searching for relevant organizations",          order: 2 },
  { id: "FINDING_WEBSITES", label: "Finding official websites",       description: "Identifying official website URLs",             order: 3 },
  { id: "CRAWLING",         label: "Crawling websites",               description: "Visiting and reading public website pages",     order: 4 },
  { id: "EXTRACTING",       label: "Extracting contact information",  description: "Parsing phones, emails, and addresses",         order: 5 },
  { id: "CLEANING",         label: "Cleaning data",                   description: "Normalizing and formatting extracted data",     order: 6 },
  { id: "DEDUPLICATING",    label: "Removing duplicates",             description: "Merging duplicate organization records",        order: 7 },
  { id: "VERIFYING",        label: "Verifying leads",                 description: "Assigning data confidence scores",              order: 8 },
  { id: "SAVING",           label: "Saving results",                  description: "Persisting leads to the database",              order: 9 },
  { id: "COMPLETED",        label: "Completed",                       description: "All leads are ready to view",                   order: 10 },
];

// ─── Core progress type ──────────────────────────────────────────────────────

export interface TaskProgress {
  taskId: string;
  status: ScrapingTaskStatus;
  location: string;
  keyword: string;
  searchRadius: string;
  maxResults: number;
  maxPagesPerSite: number;
  progress: number;           // 0–100
  currentStage: ScrapingStage;
  resultsDiscovered: number;
  websitesFound: number;
  websitesCrawled: number;
  phonesFound: number;
  emailsFound: number;
  addressesFound: number;
  duplicatesRemoved: number;
  failedWebsites: number;
  blockedWebsites: number;
  timeoutWebsites: number;
  startedAt: string;          // ISO string
  completedAt?: string;
  failureReason?: string;
}

// ─── Activity log ────────────────────────────────────────────────────────────

export interface ActivityEntry {
  id: string;
  timestamp: string;          // display string e.g. "10:42:08"
  message: string;
  type: "info" | "success" | "warning" | "error";
}

// ─── Website processing ──────────────────────────────────────────────────────

export type WebsiteStatus = "SUCCESS" | "PROCESSING" | "TIMEOUT" | "BLOCKED" | "FAILED";

export interface WebsiteEntry {
  organization: string;
  domain: string;
  status: WebsiteStatus;
  reason?: string;
}
