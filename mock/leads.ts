import type {
  Lead,
  LeadFilterState,
  LeadSortField,
  SortDirection,
} from "@/types/lead";

export const MOCK_LEADS: Lead[] = [
  {
    id: "lead-001",
    organizationName: "Pondicherry Public School",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605001",
    phone: "+91 98423 45678",
    alternatePhone: "0413-2245678",
    email: "info@pondicherrypublicschool.org",
    website: "https://pondicherrypublicschool.org",
    address: "No. 45, East Coast Road, Lawspet, Puducherry",
    whatsapp: "+91 98423 45678",
    contactPerson: "Dr. K. Swaminathan",
    designation: "Principal",
    verification: {
      status: "HIGH",
      fieldsFound: 8,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    socialLinks: [
      { platform: "facebook", url: "https://facebook.com/pondicherrypublicschool" },
      { platform: "youtube", url: "https://youtube.com/@pondischool" },
    ],
    sourcePages: [
      { field: "phone", url: "https://pondicherrypublicschool.org/contact", pageTitle: "Contact Us" },
      { field: "email", url: "https://pondicherrypublicschool.org/contact", pageTitle: "Contact Us" },
      { field: "address", url: "https://pondicherrypublicschool.org/reach-us", pageTitle: "Reach Us" },
    ],
  },
  {
    id: "lead-002",
    organizationName: "Little Flowers Senior Secondary School",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605008",
    phone: "+91 94432 18902",
    email: "admissions@littleflowers.ac.in",
    website: "https://littleflowers.ac.in",
    address: "12, Subbaiah Salai, Puducherry",
    whatsapp: "+91 94432 18902",
    contactPerson: "Mrs. Revathi Raman",
    designation: "Headmistress",
    verification: {
      status: "HIGH",
      fieldsFound: 7,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    socialLinks: [
      { platform: "instagram", url: "https://instagram.com/littleflowerscbse" },
    ],
    sourcePages: [
      { field: "phone", url: "https://littleflowers.ac.in/contact-us", pageTitle: "Contact" },
      { field: "email", url: "https://littleflowers.ac.in/admissions", pageTitle: "Admissions 2026" },
    ],
  },
  {
    id: "lead-003",
    organizationName: "Holy Cross Academy",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605010",
    phone: "+91 98940 76543",
    email: "holycrosspondi@gmail.com",
    website: "https://holycrosspondi.edu",
    address: "Villupuram Main Road, Moolakulam, Puducherry",
    verification: {
      status: "MEDIUM",
      fieldsFound: 5,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    sourcePages: [
      { field: "phone", url: "https://holycrosspondi.edu/contact", pageTitle: "Contact Information" },
      { field: "email", url: "https://holycrosspondi.edu/about", pageTitle: "About Us" },
    ],
  },
  {
    id: "lead-004",
    organizationName: "St. Joseph's Higher Secondary School",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605001",
    phone: "0413-2334455",
    alternatePhone: "+91 97890 12345",
    website: "https://stjosephpondy.com",
    address: "Rue Romain Rolland, White Town, Puducherry",
    whatsapp: "+91 97890 12345",
    contactPerson: "Fr. A. Lawrence",
    designation: "Secretary & Correspondent",
    verification: {
      status: "MEDIUM",
      fieldsFound: 6,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    sourcePages: [
      { field: "phone", url: "https://stjosephpondy.com/contact", pageTitle: "Contact Page" },
    ],
  },
  {
    id: "lead-005",
    organizationName: "Providence International School",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605107",
    website: "https://providenceschool.in",
    address: "Auroville Post, Bommayapalayam, Puducherry",
    verification: {
      status: "LOW",
      fieldsFound: 3,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    sourcePages: [
      { field: "address", url: "https://providenceschool.in/about", pageTitle: "Campus Details" },
    ],
  },
  {
    id: "lead-006",
    organizationName: "Achariya Siksha Mandir",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605004",
    phone: "+91 98432 99881",
    email: "principal@achariya.org",
    website: "https://achariya.org",
    address: "Achariya Campus, Villianur, Puducherry",
    whatsapp: "+91 98432 99881",
    contactPerson: "J. Aravind",
    designation: "Director of Admissions",
    verification: {
      status: "HIGH",
      fieldsFound: 8,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    socialLinks: [
      { platform: "facebook", url: "https://facebook.com/achariyagroup" },
      { platform: "linkedin", url: "https://linkedin.com/school/achariya" },
    ],
    sourcePages: [
      { field: "phone", url: "https://achariya.org/contact", pageTitle: "Get in Touch" },
      { field: "email", url: "https://achariya.org/admissions", pageTitle: "Admissions Desk" },
    ],
  },
  {
    id: "lead-007",
    organizationName: "Sri Aurobindo International Centre of Education",
    category: "CBSE School",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605002",
    phone: "0413-2233667",
    email: "saice@sriaurobindoashram.org",
    website: "https://sriaurobindoschool.com",
    address: "Rue de la Marine, Puducherry",
    contactPerson: "Manoj Das",
    designation: "Academic Dean",
    verification: {
      status: "HIGH",
      fieldsFound: 7,
      totalFields: 8,
    },
    scrapedDate: "Sep 10, 2026",
    taskId: "TASK-000124",
    sourcePages: [
      { field: "phone", url: "https://sriaurobindoschool.com/info", pageTitle: "General Inquiries" },
      { field: "email", url: "https://sriaurobindoschool.com/contact", pageTitle: "Office Contacts" },
    ],
  },
  {
    id: "lead-008",
    organizationName: "Madras Institute of Technology",
    category: "College",
    location: "Chennai",
    city: "Chennai",
    state: "Tamil Nadu",
    pincode: "600044",
    phone: "+91 94440 55667",
    email: "dean@mitindia.edu",
    website: "https://mitindia.edu",
    address: "Chromepet, Chennai, Tamil Nadu",
    contactPerson: "Dr. T. Thyagarajan",
    designation: "Dean & Professor",
    verification: {
      status: "HIGH",
      fieldsFound: 7,
      totalFields: 8,
    },
    scrapedDate: "Sep 09, 2026",
    taskId: "TASK-000123",
    socialLinks: [
      { platform: "linkedin", url: "https://linkedin.com/school/mit-anna-university" },
    ],
    sourcePages: [
      { field: "phone", url: "https://mitindia.edu/contact", pageTitle: "Contact Page" },
      { field: "email", url: "https://mitindia.edu/administration", pageTitle: "Administration" },
    ],
  },
  {
    id: "lead-009",
    organizationName: "SSN College of Engineering",
    category: "College",
    location: "Chennai",
    city: "Chennai",
    state: "Tamil Nadu",
    pincode: "603110",
    phone: "+91 98401 22334",
    alternatePhone: "044-27469700",
    email: "info@ssn.edu.in",
    website: "https://ssn.edu.in",
    address: "Rajiv Gandhi Salai (OMR), Kalavakkam, Chennai",
    whatsapp: "+91 98401 22334",
    contactPerson: "Dr. V. E. Annamalai",
    designation: "Principal",
    verification: {
      status: "HIGH",
      fieldsFound: 8,
      totalFields: 8,
    },
    scrapedDate: "Sep 09, 2026",
    taskId: "TASK-000123",
    socialLinks: [
      { platform: "facebook", url: "https://facebook.com/ssnce" },
      { platform: "youtube", url: "https://youtube.com/@ssnedu" },
    ],
    sourcePages: [
      { field: "phone", url: "https://ssn.edu.in/contact-us", pageTitle: "Contact Directory" },
      { field: "email", url: "https://ssn.edu.in/reach-us", pageTitle: "Campus Reach" },
    ],
  },
  {
    id: "lead-010",
    organizationName: "PSG College of Technology",
    category: "College",
    location: "Coimbatore",
    city: "Coimbatore",
    state: "Tamil Nadu",
    pincode: "641004",
    phone: "0422-4344777",
    email: "principal@psgtech.edu",
    website: "https://psgtech.edu",
    address: "Avinashi Road, Peelamedu, Coimbatore",
    contactPerson: "Dr. K. Prakasan",
    designation: "Principal",
    verification: {
      status: "HIGH",
      fieldsFound: 7,
      totalFields: 8,
    },
    scrapedDate: "Sep 09, 2026",
    taskId: "TASK-000123",
    sourcePages: [
      { field: "phone", url: "https://psgtech.edu/contact.php", pageTitle: "Office of Principal" },
    ],
  },
  {
    id: "lead-011",
    organizationName: "Ganga Hospital & Research Centre",
    category: "Hospital",
    location: "Coimbatore",
    city: "Coimbatore",
    state: "Tamil Nadu",
    pincode: "641043",
    phone: "+91 98422 11223",
    alternatePhone: "0422-2485000",
    email: "enquiry@gangahospital.com",
    website: "https://gangahospital.com",
    address: "313, Mettupalayam Road, Coimbatore",
    whatsapp: "+91 98422 11223",
    contactPerson: "Dr. S. Rajasekaran",
    designation: "Chairman & Head of Orthopaedics",
    verification: {
      status: "HIGH",
      fieldsFound: 8,
      totalFields: 8,
    },
    scrapedDate: "Sep 09, 2026",
    taskId: "TASK-000122",
    socialLinks: [
      { platform: "facebook", url: "https://facebook.com/gangahospitalcbe" },
      { platform: "youtube", url: "https://youtube.com/@gangahospital" },
    ],
    sourcePages: [
      { field: "phone", url: "https://gangahospital.com/contact", pageTitle: "24x7 Help Desk" },
      { field: "email", url: "https://gangahospital.com/appointments", pageTitle: "Appointments" },
    ],
  },
  {
    id: "lead-012",
    organizationName: "KG Hospital & Medical Institute",
    category: "Hospital",
    location: "Coimbatore",
    city: "Coimbatore",
    state: "Tamil Nadu",
    pincode: "641018",
    phone: "0422-2212121",
    email: "info@kghospital.com",
    website: "https://kghospital.com",
    address: "Government Arts College Road, Coimbatore",
    verification: {
      status: "MEDIUM",
      fieldsFound: 5,
      totalFields: 8,
    },
    scrapedDate: "Sep 09, 2026",
    taskId: "TASK-000122",
    sourcePages: [
      { field: "phone", url: "https://kghospital.com/contact-us", pageTitle: "Hospital Desk" },
    ],
  },
  {
    id: "lead-013",
    organizationName: "Mindfire Solutions Pvt Ltd",
    category: "IT Company",
    location: "Bangalore",
    city: "Bangalore",
    state: "Karnataka",
    pincode: "560066",
    phone: "+91 80 4123 4567",
    email: "contact@mindfiresolutions.com",
    website: "https://mindfiresolutions.com",
    address: "ITPL Main Road, Whitefield, Bangalore",
    whatsapp: "+91 99000 88776",
    contactPerson: "Vivek Sharma",
    designation: "VP Business Development",
    verification: {
      status: "HIGH",
      fieldsFound: 8,
      totalFields: 8,
    },
    scrapedDate: "Sep 08, 2026",
    taskId: "TASK-000120",
    socialLinks: [
      { platform: "linkedin", url: "https://linkedin.com/company/mindfire-solutions" },
      { platform: "twitter", url: "https://x.com/mindfire" },
    ],
    sourcePages: [
      { field: "phone", url: "https://mindfiresolutions.com/contact", pageTitle: "Global Contact" },
      { field: "email", url: "https://mindfiresolutions.com/inquiry", pageTitle: "Business Inquiries" },
    ],
  },
  {
    id: "lead-014",
    organizationName: "CloudPulse Technologies",
    category: "IT Company",
    location: "Bangalore",
    city: "Bangalore",
    state: "Karnataka",
    pincode: "560100",
    email: "hello@cloudpulse.io",
    website: "https://cloudpulse.io",
    address: "Electronic City Phase 1, Bangalore",
    verification: {
      status: "MEDIUM",
      fieldsFound: 4,
      totalFields: 8,
    },
    scrapedDate: "Sep 08, 2026",
    taskId: "TASK-000120",
    sourcePages: [
      { field: "email", url: "https://cloudpulse.io/team", pageTitle: "Meet the Team" },
    ],
  },
  {
    id: "lead-015",
    organizationName: "Ananda Bhavan Heritage Restaurant",
    category: "Restaurant",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605001",
    phone: "+91 98421 77665",
    address: "15, Bussy Street, Heritage Town, Puducherry",
    whatsapp: "+91 98421 77665",
    contactPerson: "M. Shanmugam",
    designation: "General Manager",
    verification: {
      status: "MEDIUM",
      fieldsFound: 5,
      totalFields: 8,
    },
    scrapedDate: "Sep 07, 2026",
    taskId: "TASK-000119",
    sourcePages: [
      { field: "phone", url: "https://anandabhavanpondy.in/contact", pageTitle: "Reservations" },
    ],
  },
  {
    id: "lead-016",
    organizationName: "Le Dupleix Dining & Lounge",
    category: "Restaurant",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605001",
    phone: "0413-2226999",
    email: "dine@ledupleix.com",
    website: "https://ledupleix.com",
    address: "5, Rue de la Caserne, White Town, Puducherry",
    contactPerson: "Christophe Martin",
    designation: "F&B Director",
    verification: {
      status: "HIGH",
      fieldsFound: 7,
      totalFields: 8,
    },
    scrapedDate: "Sep 07, 2026",
    taskId: "TASK-000119",
    socialLinks: [
      { platform: "instagram", url: "https://instagram.com/ledupleixpondy" },
    ],
    sourcePages: [
      { field: "phone", url: "https://ledupleix.com/dining", pageTitle: "Restaurant & Bar" },
      { field: "email", url: "https://ledupleix.com/contact-us", pageTitle: "Contact & Table Booking" },
    ],
  },
  {
    id: "lead-017",
    organizationName: "Apex Advocates & Legal Consultants",
    category: "Law Firm",
    location: "Chennai",
    city: "Chennai",
    state: "Tamil Nadu",
    pincode: "600104",
    phone: "+91 94441 88990",
    email: "cases@apexlegal.in",
    website: "https://apexlegal.in",
    address: "High Court Chambers, Parry's Corner, Chennai",
    contactPerson: "Adv. K. Balasubramanian",
    designation: "Senior Managing Partner",
    verification: {
      status: "HIGH",
      fieldsFound: 7,
      totalFields: 8,
    },
    scrapedDate: "Sep 08, 2026",
    taskId: "TASK-000121",
    socialLinks: [
      { platform: "linkedin", url: "https://linkedin.com/company/apex-legal-chennai" },
    ],
    sourcePages: [
      { field: "phone", url: "https://apexlegal.in/consultation", pageTitle: "Book Legal Consultation" },
    ],
  },
  {
    id: "lead-018",
    organizationName: "Venkateshwara Dental Hospital",
    category: "Hospital",
    location: "Puducherry",
    city: "Puducherry",
    state: "Puducherry",
    pincode: "605102",
    phone: "0413-2644400",
    website: "https://svdentalpondy.edu.in",
    address: "Ariyur, Puducherry",
    verification: {
      status: "LOW",
      fieldsFound: 4,
      totalFields: 8,
    },
    scrapedDate: "Sep 06, 2026",
    taskId: "TASK-000118",
    sourcePages: [
      { field: "phone", url: "https://svdentalpondy.edu.in/contact", pageTitle: "Contact Page" },
    ],
  },
];

// ─── Query & Filtering Utilities ──────────────────────────────────────────────

export function searchLeads(leads: Lead[], query: string): Lead[] {
  if (!query || !query.trim()) return leads;
  const q = query.toLowerCase().trim();

  return leads.filter((lead) => {
    return (
      lead.organizationName.toLowerCase().includes(q) ||
      lead.category.toLowerCase().includes(q) ||
      lead.location.toLowerCase().includes(q) ||
      (lead.phone && lead.phone.toLowerCase().includes(q)) ||
      (lead.email && lead.email.toLowerCase().includes(q)) ||
      (lead.website && lead.website.toLowerCase().includes(q)) ||
      (lead.contactPerson && lead.contactPerson.toLowerCase().includes(q)) ||
      (lead.address && lead.address.toLowerCase().includes(q))
    );
  });
}

export function filterLeads(leads: Lead[], filters: Partial<LeadFilterState>): Lead[] {
  return leads.filter((lead) => {
    // Category filter
    if (filters.categories && filters.categories.length > 0) {
      if (!filters.categories.includes(lead.category)) return false;
    }

    // Location filter
    if (filters.locations && filters.locations.length > 0) {
      if (!filters.locations.includes(lead.location)) return false;
    }

    // Verification filter
    if (filters.verifications && filters.verifications.length > 0) {
      if (!filters.verifications.includes(lead.verification.status)) return false;
    }

    // Data Available flags
    if (filters.hasPhone && !lead.phone) return false;
    if (filters.hasEmail && !lead.email) return false;
    if (filters.hasWebsite && !lead.website) return false;
    if (filters.hasWhatsApp && !lead.whatsapp) return false;
    if (filters.hasContactPerson && !lead.contactPerson) return false;
    if (filters.hasSocialLinks && (!lead.socialLinks || lead.socialLinks.length === 0)) return false;

    // Task filter
    if (filters.taskId && filters.taskId.trim()) {
      if (lead.taskId.toLowerCase() !== filters.taskId.toLowerCase().trim()) return false;
    }

    return true;
  });
}

export function sortLeads(
  leads: Lead[],
  field: LeadSortField,
  direction: SortDirection
): Lead[] {
  const sorted = [...leads];
  const order = direction === "asc" ? 1 : -1;

  sorted.sort((a, b) => {
    switch (field) {
      case "organizationName":
        return order * a.organizationName.localeCompare(b.organizationName);
      case "location":
        return order * a.location.localeCompare(b.location);
      case "category":
        return order * a.category.localeCompare(b.category);
      case "verification": {
        const weight: Record<string, number> = { HIGH: 3, MEDIUM: 2, LOW: 1 };
        return order * ((weight[a.verification.status] || 0) - (weight[b.verification.status] || 0));
      }
      case "scrapedDate":
        return order * (new Date(a.scrapedDate).getTime() - new Date(b.scrapedDate).getTime());
      default:
        return 0;
    }
  });

  return sorted;
}

export function paginateLeads(
  leads: Lead[],
  page: number,
  pageSize: number
): { data: Lead[]; total: number; totalPages: number } {
  const total = leads.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(Math.max(1, page), totalPages);
  const start = (currentPage - 1) * pageSize;
  const data = leads.slice(start, start + pageSize);

  return {
    data,
    total,
    totalPages,
  };
}

// ─── Individual Lead Access & Storage ─────────────────────────────────────────

const STORAGE_OVERRIDE_KEY = "leadscout_lead_overrides";

export function getLeadById(id: string): Lead | undefined {
  if (!id) return undefined;

  // Check localStorage for user edits
  if (typeof window !== "undefined") {
    try {
      const overridesRaw = localStorage.getItem(STORAGE_OVERRIDE_KEY);
      if (overridesRaw) {
        const overrides: Record<string, Lead> = JSON.parse(overridesRaw);
        if (overrides[id]) {
          return overrides[id];
        }
      }
    } catch {}
  }

  return MOCK_LEADS.find((l) => l.id.toLowerCase() === id.toLowerCase());
}

export function saveLeadToStorage(updatedLead: Lead): void {
  if (typeof window === "undefined") return;
  try {
    const overridesRaw = localStorage.getItem(STORAGE_OVERRIDE_KEY);
    const overrides: Record<string, Lead> = overridesRaw ? JSON.parse(overridesRaw) : {};
    overrides[updatedLead.id] = updatedLead;
    localStorage.setItem(STORAGE_OVERRIDE_KEY, JSON.stringify(overrides));
  } catch {}
}

export function deleteLeadFromStorage(id: string): void {
  if (typeof window === "undefined") return;
  try {
    const overridesRaw = localStorage.getItem(STORAGE_OVERRIDE_KEY);
    if (overridesRaw) {
      const overrides: Record<string, Lead> = JSON.parse(overridesRaw);
      delete overrides[id];
      localStorage.setItem(STORAGE_OVERRIDE_KEY, JSON.stringify(overrides));
    }
  } catch {}
}
