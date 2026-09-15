import type { TaskStatus } from "@/types";

// ─── Metric Cards ────────────────────────────────────────────────────────────

export interface MetricData {
  id: string;
  label: string;
  value: string;
  rawValue: number;
  change: string;
  changePositive: boolean;
  changeLabel: string;
}

export const dashboardMetrics: MetricData[] = [
  {
    id: "total_leads",
    label: "Total Leads",
    value: "12,480",
    rawValue: 12480,
    change: "+12.4%",
    changePositive: true,
    changeLabel: "this month",
  },
  {
    id: "websites_discovered",
    label: "Websites Discovered",
    value: "4,820",
    rawValue: 4820,
    change: "+8.2%",
    changePositive: true,
    changeLabel: "this month",
  },
  {
    id: "verified_leads",
    label: "Verified Leads",
    value: "8,940",
    rawValue: 8940,
    change: "+15.6%",
    changePositive: true,
    changeLabel: "this month",
  },
  {
    id: "scraping_tasks",
    label: "Scraping Tasks",
    value: "126",
    rawValue: 126,
    change: "+9",
    changePositive: true,
    changeLabel: "this week",
  },
];

// ─── Recent Tasks ─────────────────────────────────────────────────────────────

export interface RecentTask {
  taskId: string;
  keyword: string;
  location: string;
  results: number;
  status: TaskStatus;
  createdAt: string;
}

export const recentTasks: RecentTask[] = [
  {
    taskId: "TASK-000124",
    keyword: "CBSE Schools",
    location: "Puducherry",
    results: 100,
    status: "COMPLETED",
    createdAt: "Sep 10, 2026",
  },
  {
    taskId: "TASK-000123",
    keyword: "Engineering Colleges",
    location: "Chennai",
    results: 150,
    status: "COMPLETED",
    createdAt: "Sep 9, 2026",
  },
  {
    taskId: "TASK-000122",
    keyword: "Hospitals",
    location: "Coimbatore",
    results: 80,
    status: "RUNNING",
    createdAt: "Sep 9, 2026",
  },
  {
    taskId: "TASK-000121",
    keyword: "Law Firms",
    location: "Bangalore",
    results: 65,
    status: "COMPLETED",
    createdAt: "Sep 8, 2026",
  },
  {
    taskId: "TASK-000120",
    keyword: "IT Companies",
    location: "Hyderabad",
    results: 200,
    status: "COMPLETED",
    createdAt: "Sep 7, 2026",
  },
  {
    taskId: "TASK-000119",
    keyword: "Dental Clinics",
    location: "Mumbai",
    results: 0,
    status: "RUNNING",
    createdAt: "Sep 7, 2026",
  },
];

// ─── Leads by Category ────────────────────────────────────────────────────────

export interface CategoryData {
  category: string;
  leads: number;
  color: string;
}

export const leadsByCategory: CategoryData[] = [
  { category: "Education", leads: 3840, color: "#BE0B31" },
  { category: "Healthcare", leads: 2610, color: "#141414" },
  { category: "Technology", leads: 2200, color: "#1E6541" },
  { category: "Legal", leads: 1520, color: "#C88A2C" },
  { category: "Finance", leads: 1180, color: "#D95338" },
  { category: "Others", leads: 1130, color: "#636059" },
];

// ─── Leads by Location ────────────────────────────────────────────────────────

export interface LocationData {
  location: string;
  leads: number;
}

export const leadsByLocation: LocationData[] = [
  { location: "Chennai", leads: 3200 },
  { location: "Bangalore", leads: 2800 },
  { location: "Hyderabad", leads: 2100 },
  { location: "Mumbai", leads: 1900 },
  { location: "Puducherry", leads: 980 },
  { location: "Coimbatore", leads: 760 },
  { location: "Others", leads: 740 },
];
