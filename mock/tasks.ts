import type {
  TaskItem,
  TaskFilterState,
  TaskSortField,
  SortDirection,
} from "@/types/task";

export const MOCK_TASKS: TaskItem[] = [
  {
    id: "TASK-000124",
    keyword: "CBSE Schools",
    location: "Puducherry",
    searchRadius: "25",
    maxResults: 100,
    maxPagesPerSite: 20,
    selectedFields: ["phone", "email", "website", "address", "whatsapp", "contact_person"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 100,
    verifiedCount: 61,
    createdAt: "Sep 10, 2026, 10:42 AM",
    duration: "2m 14s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000123",
    keyword: "Engineering Colleges",
    location: "Chennai",
    searchRadius: "50",
    maxResults: 150,
    maxPagesPerSite: 25,
    selectedFields: ["phone", "email", "website", "contact_person"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 150,
    verifiedCount: 94,
    createdAt: "Sep 09, 2026, 03:15 PM",
    duration: "3m 42s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000122",
    keyword: "Hospitals & Clinics",
    location: "Coimbatore",
    searchRadius: "25",
    maxResults: 80,
    maxPagesPerSite: 15,
    selectedFields: ["phone", "email", "website", "address", "whatsapp"],
    status: "RUNNING",
    progress: 82,
    currentStage: "Extracting contact information",
    resultsCount: 68,
    verifiedCount: 48,
    createdAt: "Sep 09, 2026, 11:30 AM",
    duration: "Running...",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000121",
    keyword: "Restaurants & Cafes",
    location: "Madurai",
    searchRadius: "15",
    maxResults: 120,
    maxPagesPerSite: 10,
    selectedFields: ["phone", "email", "website", "whatsapp"],
    status: "FAILED",
    progress: 0,
    currentStage: "Failed",
    resultsCount: 0,
    verifiedCount: 0,
    createdAt: "Sep 08, 2026, 05:20 PM",
    duration: "45s",
    failureReason: "Unable to complete task because directory discovery service was unreachable.",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000120",
    keyword: "IT Companies & Startups",
    location: "Bangalore",
    searchRadius: "25",
    maxResults: 200,
    maxPagesPerSite: 30,
    selectedFields: ["phone", "email", "website", "social_links", "contact_person"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 200,
    verifiedCount: 142,
    createdAt: "Sep 08, 2026, 01:10 PM",
    duration: "4m 18s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000119",
    keyword: "Law Firms & Advocates",
    location: "Chennai",
    searchRadius: "20",
    maxResults: 50,
    maxPagesPerSite: 15,
    selectedFields: ["phone", "email", "website", "contact_person"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 50,
    verifiedCount: 32,
    createdAt: "Sep 07, 2026, 04:45 PM",
    duration: "1m 55s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000118",
    keyword: "Dental Clinics",
    location: "Puducherry",
    searchRadius: "10",
    maxResults: 40,
    maxPagesPerSite: 10,
    selectedFields: ["phone", "email", "website", "address"],
    status: "CANCELLED",
    progress: 25,
    currentStage: "Cancelled",
    resultsCount: 12,
    verifiedCount: 6,
    createdAt: "Sep 06, 2026, 02:18 PM",
    duration: "1m 02s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000117",
    keyword: "Real Estate Developers",
    location: "Bangalore",
    searchRadius: "30",
    maxResults: 120,
    maxPagesPerSite: 20,
    selectedFields: ["phone", "email", "website", "contact_person", "address"],
    status: "RUNNING",
    progress: 54,
    currentStage: "Crawling websites",
    resultsCount: 52,
    verifiedCount: 34,
    createdAt: "Sep 06, 2026, 10:05 AM",
    duration: "Running...",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000116",
    keyword: "Manufacturing Units",
    location: "Coimbatore",
    searchRadius: "40",
    maxResults: 90,
    maxPagesPerSite: 15,
    selectedFields: ["phone", "email", "website", "address"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 90,
    verifiedCount: 58,
    createdAt: "Sep 05, 2026, 03:50 PM",
    duration: "2m 45s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000115",
    keyword: "International Schools",
    location: "Chennai",
    searchRadius: "25",
    maxResults: 75,
    maxPagesPerSite: 20,
    selectedFields: ["phone", "email", "website", "contact_person", "whatsapp"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 75,
    verifiedCount: 52,
    createdAt: "Sep 05, 2026, 09:12 AM",
    duration: "2m 08s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000114",
    keyword: "Diagnostic Centres",
    location: "Madurai",
    searchRadius: "20",
    maxResults: 60,
    maxPagesPerSite: 10,
    selectedFields: ["phone", "email", "address"],
    status: "FAILED",
    progress: 0,
    currentStage: "Failed",
    resultsCount: 0,
    verifiedCount: 0,
    createdAt: "Sep 04, 2026, 04:30 PM",
    duration: "1m 15s",
    failureReason: "Connection timeout during regional organization indexing.",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000113",
    keyword: "Boutique Hotels",
    location: "Puducherry",
    searchRadius: "15",
    maxResults: 40,
    maxPagesPerSite: 15,
    selectedFields: ["phone", "email", "website", "address", "whatsapp"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 40,
    verifiedCount: 28,
    createdAt: "Sep 04, 2026, 11:25 AM",
    duration: "1m 30s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000112",
    keyword: "Pharmacy Stores",
    location: "Coimbatore",
    searchRadius: "20",
    maxResults: 65,
    maxPagesPerSite: 10,
    selectedFields: ["phone", "address", "whatsapp"],
    status: "RUNNING",
    progress: 30,
    currentStage: "Finding official websites",
    resultsCount: 22,
    verifiedCount: 14,
    createdAt: "Sep 03, 2026, 06:10 PM",
    duration: "Running...",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000111",
    keyword: "Chartered Accountants",
    location: "Bangalore",
    searchRadius: "25",
    maxResults: 110,
    maxPagesPerSite: 15,
    selectedFields: ["phone", "email", "website", "contact_person"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 110,
    verifiedCount: 85,
    createdAt: "Sep 03, 2026, 01:40 PM",
    duration: "3m 10s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000110",
    keyword: "Logistics & Transport",
    location: "Chennai",
    searchRadius: "30",
    maxResults: 80,
    maxPagesPerSite: 15,
    selectedFields: ["phone", "email", "website", "address"],
    status: "CANCELLED",
    progress: 18,
    currentStage: "Cancelled",
    resultsCount: 8,
    verifiedCount: 3,
    createdAt: "Sep 02, 2026, 03:22 PM",
    duration: "55s",
    createdBy: "Sarah Chen",
  },
  {
    id: "TASK-000109",
    keyword: "Fitness & Gym Centers",
    location: "Puducherry",
    searchRadius: "15",
    maxResults: 45,
    maxPagesPerSite: 10,
    selectedFields: ["phone", "email", "address", "whatsapp"],
    status: "COMPLETED",
    progress: 100,
    currentStage: "Completed",
    resultsCount: 45,
    verifiedCount: 30,
    createdAt: "Sep 02, 2026, 10:15 AM",
    duration: "1m 40s",
    createdBy: "Sarah Chen",
  },
];

// ─── Query & Filtering Utilities ──────────────────────────────────────────────

export function searchTasks(tasks: TaskItem[], query: string): TaskItem[] {
  if (!query || !query.trim()) return tasks;
  const q = query.toLowerCase().trim();

  return tasks.filter((t) => {
    return (
      t.id.toLowerCase().includes(q) ||
      t.keyword.toLowerCase().includes(q) ||
      t.location.toLowerCase().includes(q)
    );
  });
}

export function filterTasks(tasks: TaskItem[], filters: Partial<TaskFilterState>): TaskItem[] {
  return tasks.filter((t) => {
    // Status filter
    if (filters.status && filters.status.length > 0) {
      if (!filters.status.includes(t.status)) return false;
    }

    // Location filter
    if (filters.locations && filters.locations.length > 0) {
      if (!filters.locations.includes(t.location)) return false;
    }

    // Has Results filter
    if (filters.hasResults === "has_results" && t.resultsCount === 0) return false;
    if (filters.hasResults === "no_results" && t.resultsCount > 0) return false;

    return true;
  });
}

export function sortTasks(
  tasks: TaskItem[],
  field: TaskSortField,
  direction: SortDirection
): TaskItem[] {
  const sorted = [...tasks];
  const order = direction === "asc" ? 1 : -1;

  sorted.sort((a, b) => {
    switch (field) {
      case "keyword":
        return order * a.keyword.localeCompare(b.keyword);
      case "location":
        return order * a.location.localeCompare(b.location);
      case "resultsCount":
        return order * (a.resultsCount - b.resultsCount);
      case "status":
        return order * a.status.localeCompare(b.status);
      case "duration":
        return order * a.duration.localeCompare(b.duration);
      case "createdAt":
      default:
        return order * (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
    }
  });

  return sorted;
}

export function paginateTasks(
  tasks: TaskItem[],
  page: number,
  pageSize: number
): { data: TaskItem[]; total: number; totalPages: number } {
  const total = tasks.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(Math.max(1, page), totalPages);
  const start = (currentPage - 1) * pageSize;
  const data = tasks.slice(start, start + pageSize);

  return {
    data,
    total,
    totalPages,
  };
}

// ─── LocalStorage Persistence Helpers ─────────────────────────────────────────

const TASKS_STORAGE_KEY = "leadscout_tasks_list";

export function loadTasksFromStorage(): TaskItem[] {
  if (typeof window === "undefined") return MOCK_TASKS;
  try {
    const raw = localStorage.getItem(TASKS_STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch {}
  return MOCK_TASKS;
}

export function saveTasksToStorage(tasks: TaskItem[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(TASKS_STORAGE_KEY, JSON.stringify(tasks));
  } catch {}
}
