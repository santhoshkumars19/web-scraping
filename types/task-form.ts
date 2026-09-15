import { z } from "zod";

// ─── All extractable data fields ──────────────────────────────────────────────

export const DATA_FIELD_GROUPS = [
  {
    id: "organization",
    label: "Organization Details",
    fields: [
      { id: "name", label: "Organization Name" },
      { id: "category", label: "Category" },
      { id: "website", label: "Website" },
      { id: "address", label: "Address" },
      { id: "city", label: "City" },
      { id: "state", label: "State" },
      { id: "pincode", label: "Pincode" },
    ],
  },
  {
    id: "contact",
    label: "Contact Details",
    fields: [
      { id: "phone", label: "Phone Number" },
      { id: "alternate_phone", label: "Alternate Phone" },
      { id: "email", label: "Email" },
      { id: "whatsapp", label: "WhatsApp" },
      { id: "contact_person", label: "Contact Person" },
      { id: "designation", label: "Designation" },
    ],
  },
  {
    id: "online",
    label: "Online Presence",
    fields: [
      { id: "facebook", label: "Facebook" },
      { id: "instagram", label: "Instagram" },
      { id: "linkedin", label: "LinkedIn" },
      { id: "youtube", label: "YouTube" },
      { id: "social_links", label: "Other Social Links" },
    ],
  },
] as const;

export const ALL_FIELD_IDS = DATA_FIELD_GROUPS.flatMap((g) =>
  g.fields.map((f) => f.id)
);

export const DEFAULT_SELECTED_FIELDS = [
  "name",
  "phone",
  "email",
  "website",
  "address",
  "whatsapp",
  "social_links",
  "contact_person",
];

export const SEARCH_RADIUS_OPTIONS = [
  { value: "5", label: "5 km" },
  { value: "10", label: "10 km" },
  { value: "25", label: "25 km" },
  { value: "50", label: "50 km" },
  { value: "100", label: "100 km" },
];

export const MAX_RESULTS_PRESETS = [25, 50, 100, 250, 500];
export const MAX_PAGES_PRESETS = [5, 10, 20, 50];
export const CRAWL_DEPTH_OPTIONS = [1, 2, 3, 5];

// ─── Zod validation schema ────────────────────────────────────────────────────
// Note: no .default() here — defaults live in DEFAULT_FORM_VALUES so that
// zodResolver types align exactly with ScrapingTaskFormData.

export const scrapingTaskSchema = z.object({
  location: z.string().min(1, "Location is required"),
  keyword: z.string().min(1, "Keyword or category is required"),
  searchRadius: z.string(),
  maxResults: z
    .number()
    .min(1, "Minimum 1")
    .max(500, "Maximum 500"),
  maxPagesPerSite: z
    .number()
    .min(1, "Minimum 1")
    .max(100, "Maximum 100"),
  selectedFields: z
    .array(z.string())
    .min(1, "Select at least one data field"),
  crawlDepth: z.number().min(1).max(5),
  followInternalLinks: z.boolean(),
  prioritizeContact: z.boolean(),
  prioritizeAbout: z.boolean(),
  prioritizeAdmissions: z.boolean(),
  prioritizeStaffManagement: z.boolean(),
});

// ─── TypeScript type ──────────────────────────────────────────────────────────

export type ScrapingTaskFormData = z.infer<typeof scrapingTaskSchema>;

export const DEFAULT_FORM_VALUES: ScrapingTaskFormData = {
  location: "",
  keyword: "",
  searchRadius: "25",
  maxResults: 100,
  maxPagesPerSite: 20,
  selectedFields: DEFAULT_SELECTED_FIELDS,
  crawlDepth: 3,
  followInternalLinks: true,
  prioritizeContact: true,
  prioritizeAbout: true,
  prioritizeAdmissions: true,
  prioritizeStaffManagement: true,
};

// ─── Task ID generator ────────────────────────────────────────────────────────

export function generateMockTaskId(): string {
  const base = 100 + Math.floor(Math.random() * 900);
  return `TASK-000${base}`;
}

// ─── Draft localStorage helpers ───────────────────────────────────────────────

const DRAFT_KEY = "leadscout_task_draft";

export function saveDraft(data: Partial<ScrapingTaskFormData>): void {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
  } catch {}
}

export function loadDraft(): Partial<ScrapingTaskFormData> | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearDraft(): void {
  try {
    localStorage.removeItem(DRAFT_KEY);
  } catch {}
}
