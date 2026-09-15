"""
app/services/extraction/patterns.py

Regex patterns, keyword lists, and domain mappings for data extraction.
"""

from __future__ import annotations

import re

# ── Phone Extraction Patterns ──────────────────────────────────────────────────

# Matches standard international and domestic formats including:
# +91 98765 43210, +91-9876543210, 0413-1234567, (080) 28450001, 9876543210
PHONE_REGEX = re.compile(
    r"""
    (?:(?:\+|00)[1-9]\d{0,2}[\s.-]*)?  # Optional country code (+91, 0091)
    (?:\(?\d{2,5}\)?[\s.-]*)?          # Optional STD/area code ((080), 0413)
    (?:\d{3,5}[\s.-]*\d{4,5})          # Core subscriber number (98765 43210, 1234567)
    """,
    re.VERBOSE,
)

TEL_LINK_REGEX = re.compile(r"^tel:([+0-9\s\-()]+)", re.IGNORECASE)

WHATSAPP_URL_REGEX = re.compile(
    r"(?:wa\.me/|api\.whatsapp\.com/send\?(?:[^&]*&)*phone=)(\+?[0-9]+)",
    re.IGNORECASE,
)

PHONE_TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("WHATSAPP", ["whatsapp", "wa.me", "chat with us", "whatsapp us"]),
    ("ADMISSIONS", ["admission", "admissions", "apply", "enrol", "enroll", "enrollment", "inquiry"]),
    ("OFFICE", ["office", "reception", "admin", "administration", "desk", "helpdesk", "front office"]),
    ("LANDLINE", ["landline", "telephone", "std", "epabx", "boardline", "board line"]),
    ("ALTERNATE", ["alternate", "alt", "secondary", "other number", "emergency", "mob2", "phone 2"]),
    ("MAIN", ["main", "general", "contact", "call us", "toll free", "tollfree", "helpline"]),
]

# ── Email Extraction Patterns ──────────────────────────────────────────────────

# Standard email regex
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Obfuscated email formats: info [at] example.com, info(at)example.com, info [AT] example [DOT] com
OBFUSCATED_EMAIL_REGEX = re.compile(
    r"\b([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\[AT\]|\(AT\)|\s+at\s+)\s*([A-Za-z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\[DOT\]|\(DOT\)|\s+dot\s+|\.)\s*([A-Za-z]{2,})\b",
    re.IGNORECASE,
)

IGNORED_EMAIL_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".pdf", ".zip", ".tar", ".woff", ".woff2", ".ttf",
}

IGNORED_EMAIL_DOMAINS = {
    "example.com", "example.org", "domain.com", "yourdomain.com",
    "email.com", "mysite.com", "sentry.io", "wixpress.com", "wordpress.org",
}

EMAIL_TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("ADMISSIONS", ["admission", "admissions", "apply", "enrol", "enroll", "prospectus"]),
    ("MANAGEMENT", ["principal", "director", "chairman", "chairperson", "dean", "founder", "trustee", "head", "correspondent"]),
    ("CONTACT", ["contact", "enquiry", "inquiry", "support", "help", "reach", "feedback"]),
    ("GENERAL", ["info", "general", "office", "mail", "admin", "school"]),
]

# ── Address & Pincode Patterns ────────────────────────────────────────────────

PINCODE_REGEX = re.compile(r"\b[1-9][0-9]{5}\b")

INDIAN_STATES_AND_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
    "Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep",
    "Puducherry", "Pondicherry",
]

# ── Contact Person & Designation Patterns ─────────────────────────────────────

DESIGNATION_KEYWORDS = [
    "Principal", "Vice Principal", "Headmaster", "Headmistress", "Director",
    "Managing Director", "Executive Director", "Dean", "Chairman", "Chairperson",
    "President", "Vice President", "Secretary", "Correspondent", "Founder",
    "Co-Founder", "Trustee", "Administrator", "Admissions Coordinator",
    "Admissions Officer", "Admissions Head", "Manager", "Registrar",
    "Academic Coordinator", "Head of School", "Chief Executive Officer",
]

# ── Social Media Platform Mappings ────────────────────────────────────────────

SOCIAL_PLATFORM_DOMAINS = [
    (re.compile(r"(?:www\.)?(?:facebook\.com|fb\.com|fb\.me)", re.IGNORECASE), "FACEBOOK"),
    (re.compile(r"(?:www\.)?instagram\.com", re.IGNORECASE), "INSTAGRAM"),
    (re.compile(r"(?:www\.)?linkedin\.com", re.IGNORECASE), "LINKEDIN"),
    (re.compile(r"(?:www\.)?(?:youtube\.com|youtu\.be)", re.IGNORECASE), "YOUTUBE"),
    (re.compile(r"(?:www\.)?(?:twitter\.com|x\.com)", re.IGNORECASE), "TWITTER"),
]
