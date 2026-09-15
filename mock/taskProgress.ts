import type {
  TaskProgress,
  ActivityEntry,
  WebsiteEntry,
  ScrapingStage,
} from "@/types/progress";

// ─── Progress keyframes ───────────────────────────────────────────────────────
// Each keyframe represents a snapshot of the task state at a given progress %.
// The simulation advances through these linearly.

interface Keyframe {
  progress: number;
  stage: ScrapingStage;
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
  activityMessage: string;
  activityType: ActivityEntry["type"];
}

export const PROGRESS_KEYFRAMES: Keyframe[] = [
  {
    progress: 5,
    stage: "CREATING_TASK",
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
    activityMessage: "Task created and queued for processing",
    activityType: "info",
  },
  {
    progress: 14,
    stage: "DISCOVERING",
    resultsDiscovered: 14,
    websitesFound: 0,
    websitesCrawled: 0,
    phonesFound: 0,
    emailsFound: 0,
    addressesFound: 0,
    duplicatesRemoved: 0,
    failedWebsites: 0,
    blockedWebsites: 0,
    timeoutWebsites: 0,
    activityMessage: "Discovery started — searching for CBSE Schools in Puducherry",
    activityType: "info",
  },
  {
    progress: 27,
    stage: "FINDING_WEBSITES",
    resultsDiscovered: 38,
    websitesFound: 28,
    websitesCrawled: 0,
    phonesFound: 0,
    emailsFound: 0,
    addressesFound: 0,
    duplicatesRemoved: 0,
    failedWebsites: 0,
    blockedWebsites: 0,
    timeoutWebsites: 0,
    activityMessage: "38 organizations discovered — identifying official websites",
    activityType: "success",
  },
  {
    progress: 39,
    stage: "CRAWLING",
    resultsDiscovered: 62,
    websitesFound: 48,
    websitesCrawled: 20,
    phonesFound: 15,
    emailsFound: 8,
    addressesFound: 17,
    duplicatesRemoved: 0,
    failedWebsites: 1,
    blockedWebsites: 0,
    timeoutWebsites: 1,
    activityMessage: "Website crawling started — processing 48 identified sites",
    activityType: "info",
  },
  {
    progress: 51,
    stage: "CRAWLING",
    resultsDiscovered: 78,
    websitesFound: 60,
    websitesCrawled: 35,
    phonesFound: 28,
    emailsFound: 19,
    addressesFound: 30,
    duplicatesRemoved: 0,
    failedWebsites: 2,
    blockedWebsites: 1,
    timeoutWebsites: 1,
    activityMessage: "35 websites crawled — extracting contact information",
    activityType: "info",
  },
  {
    progress: 63,
    stage: "EXTRACTING",
    resultsDiscovered: 88,
    websitesFound: 67,
    websitesCrawled: 47,
    phonesFound: 38,
    emailsFound: 27,
    addressesFound: 40,
    duplicatesRemoved: 0,
    failedWebsites: 3,
    blockedWebsites: 1,
    timeoutWebsites: 2,
    activityMessage: "Extracting contact details from crawled pages",
    activityType: "info",
  },
  {
    progress: 72,
    stage: "EXTRACTING",
    resultsDiscovered: 93,
    websitesFound: 70,
    websitesCrawled: 54,
    phonesFound: 46,
    emailsFound: 33,
    addressesFound: 46,
    duplicatesRemoved: 0,
    failedWebsites: 3,
    blockedWebsites: 2,
    timeoutWebsites: 1,
    activityMessage: "54 websites crawled — phone and email extraction in progress",
    activityType: "success",
  },
  {
    progress: 82,
    stage: "CLEANING",
    resultsDiscovered: 97,
    websitesFound: 72,
    websitesCrawled: 60,
    phonesFound: 51,
    emailsFound: 37,
    addressesFound: 49,
    duplicatesRemoved: 4,
    failedWebsites: 4,
    blockedWebsites: 2,
    timeoutWebsites: 2,
    activityMessage: "Cleaning and normalizing extracted data",
    activityType: "info",
  },
  {
    progress: 91,
    stage: "DEDUPLICATING",
    resultsDiscovered: 100,
    websitesFound: 72,
    websitesCrawled: 65,
    phonesFound: 53,
    emailsFound: 38,
    addressesFound: 50,
    duplicatesRemoved: 7,
    failedWebsites: 4,
    blockedWebsites: 2,
    timeoutWebsites: 2,
    activityMessage: "Duplicate records identified and merged",
    activityType: "success",
  },
  {
    progress: 96,
    stage: "VERIFYING",
    resultsDiscovered: 100,
    websitesFound: 72,
    websitesCrawled: 68,
    phonesFound: 54,
    emailsFound: 39,
    addressesFound: 51,
    duplicatesRemoved: 8,
    failedWebsites: 4,
    blockedWebsites: 2,
    timeoutWebsites: 2,
    activityMessage: "Assigning data confidence scores to leads",
    activityType: "info",
  },
  {
    progress: 100,
    stage: "COMPLETED",
    resultsDiscovered: 100,
    websitesFound: 72,
    websitesCrawled: 68,
    phonesFound: 54,
    emailsFound: 39,
    addressesFound: 51,
    duplicatesRemoved: 8,
    failedWebsites: 4,
    blockedWebsites: 2,
    timeoutWebsites: 2,
    activityMessage: "Task completed — 100 leads ready to view",
    activityType: "success",
  },
];

// ─── Mock website processing data ────────────────────────────────────────────

export const MOCK_WEBSITES: WebsiteEntry[] = [
  { organization: "ABC Senior Secondary School", domain: "abcschool.pondicherry.edu.in", status: "SUCCESS" },
  { organization: "Little Flowers CBSE School", domain: "littleflowers.ac.in", status: "SUCCESS" },
  { organization: "Pondicherry Public School", domain: "pondicherrypublicschool.org", status: "SUCCESS" },
  { organization: "Holy Cross Academy", domain: "holycrosspondi.edu", status: "SUCCESS" },
  { organization: "St. Joseph's Higher Secondary", domain: "stjosephpondy.com", status: "SUCCESS" },
  { organization: "Providence International School", domain: "providenceschool.in", status: "TIMEOUT",  reason: "Response timeout after 30s" },
  { organization: "Sri Aurobindo International", domain: "sriaurobindoschool.com", status: "BLOCKED",  reason: "Access denied by server" },
  { organization: "Velammal CBSE School", domain: "velammalpondi.edu.in", status: "SUCCESS" },
  { organization: "Tagore Vidyalaya", domain: "tagorevidyalaya.org", status: "SUCCESS" },
  { organization: "New Horizon Academy",  domain: "newhorizonschool.in",  status: "TIMEOUT",  reason: "Connection timeout" },
  { organization: "Rainbow Public School", domain: "rainbowschoolpondi.com", status: "SUCCESS" },
  { organization: "Achariya Siksha Mandir", domain: "achariyaschool.com", status: "SUCCESS" },
  { organization: "GRT Mahalakshmi School", domain: "grtschool.in", status: "FAILED", reason: "DNS resolution failed" },
  { organization: "DAV Public School", domain: "davpondicherry.in", status: "SUCCESS" },
  { organization: "Amrita Vidyalayam", domain: "amritavidyalayam.edu.in", status: "SUCCESS" },
];

// ─── Initial task state builder ───────────────────────────────────────────────

export function buildInitialTask(
  taskId: string,
  overrides?: Partial<Pick<TaskProgress, "location" | "keyword" | "searchRadius" | "maxResults" | "maxPagesPerSite">>
): TaskProgress {
  return {
    taskId,
    status: "RUNNING",
    location: overrides?.location ?? "Puducherry",
    keyword: overrides?.keyword ?? "CBSE Schools",
    searchRadius: overrides?.searchRadius ?? "25",
    maxResults: overrides?.maxResults ?? 100,
    maxPagesPerSite: overrides?.maxPagesPerSite ?? 20,
    progress: PROGRESS_KEYFRAMES[0].progress,
    currentStage: PROGRESS_KEYFRAMES[0].stage,
    resultsDiscovered: PROGRESS_KEYFRAMES[0].resultsDiscovered,
    websitesFound: PROGRESS_KEYFRAMES[0].websitesFound,
    websitesCrawled: PROGRESS_KEYFRAMES[0].websitesCrawled,
    phonesFound: PROGRESS_KEYFRAMES[0].phonesFound,
    emailsFound: PROGRESS_KEYFRAMES[0].emailsFound,
    addressesFound: PROGRESS_KEYFRAMES[0].addressesFound,
    duplicatesRemoved: PROGRESS_KEYFRAMES[0].duplicatesRemoved,
    failedWebsites: PROGRESS_KEYFRAMES[0].failedWebsites,
    blockedWebsites: PROGRESS_KEYFRAMES[0].blockedWebsites,
    timeoutWebsites: PROGRESS_KEYFRAMES[0].timeoutWebsites,
    startedAt: new Date().toISOString(),
  };
}

// ─── Initial activity log ─────────────────────────────────────────────────────

function now(): string {
  return new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function buildInitialActivity(): ActivityEntry[] {
  return [
    {
      id: "act-0",
      timestamp: now(),
      message: "Task created and queued for processing",
      type: "info",
    },
  ];
}

export function buildActivityEntry(
  keyframeIndex: number,
  keyframe: typeof PROGRESS_KEYFRAMES[0]
): ActivityEntry {
  return {
    id: `act-${keyframeIndex}`,
    timestamp: now(),
    message: keyframe.activityMessage,
    type: keyframe.activityType,
  };
}
