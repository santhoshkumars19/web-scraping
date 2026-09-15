"""
app/services/crawler/page_classifier.py

Heuristic classifier to categorize web pages and compute priority weights
based on URL path, anchor text, and page title.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# Page type keywords mapping
CLASSIFICATION_RULES: list[tuple[str, list[str]]] = [
    (
        "CONTACT",
        [
            "contact", "contact-us", "contact_us", "contactus", "reach-us",
            "get-in-touch", "enquiry", "inquiry", "feedback", "helpdesk",
        ],
    ),
    (
        "ADMISSIONS",
        [
            "admission", "admissions", "apply", "enrol", "enroll", "enrollment",
            "prospectus", "registration", "join-us", "how-to-apply",
        ],
    ),
    (
        "PRINCIPAL",
        [
            "principal", "headmaster", "director-desk", "principals-desk",
            "principal-message", "director-message", "chancellor", "dean", "founder",
        ],
    ),
    (
        "MANAGEMENT",
        [
            "management", "board", "leadership", "trustees", "governing-body",
            "committee", "administration", "directors", "executive", "board-of-governors",
        ],
    ),
    (
        "FACULTY",
        [
            "faculty", "teachers", "professors", "educators", "teaching-staff",
            "academic-staff", "instructors",
        ],
    ),
    (
        "STAFF",
        [
            "staff", "our-team", "meet-the-team", "people", "employees",
            "directory", "members",
        ],
    ),
    (
        "ABOUT",
        [
            "about", "about-us", "about_us", "aboutus", "overview", "our-story",
            "history", "who-we-are", "mission", "vision", "profile", "institution",
            "introduction",
        ],
    ),
    (
        "LOCATION",
        [
            "location", "locations", "locate", "directions", "address", "find-us",
            "map", "how-to-reach",
        ],
    ),
    (
        "INFRASTRUCTURE",
        [
            "infrastructure", "facilities", "laboratory", "library", "hostel",
            "sports", "transport", "amenities", "labs",
        ],
    ),
    (
        "BRANCH",
        [
            "branch", "branches", "campuses", "campus", "centers", "centres",
        ],
    ),
]



class PageClassifier:
    """Classifies a URL, anchor text, or page title into a standardized page_type."""

    @classmethod
    def classify(
        cls,
        url: str,
        anchor_text: str = "",
        page_title: str | None = None,
    ) -> str:
        """Classify page into one of the enum values:
        HOME, ABOUT, CONTACT, ADMISSIONS, MANAGEMENT, PRINCIPAL,
        FACULTY, STAFF, BRANCH, LOCATION, INFRASTRUCTURE, OTHER.
        """
        parsed = urlparse(url)
        path = parsed.path.strip("/").lower()

        # 1. Check for HOME page
        if not path or path in ("index.html", "index.php", "index.htm", "home", "default.aspx"):
            return "HOME"

        combined_text = f"{path} {anchor_text.lower()} {(page_title or '').lower()}"

        # 2. Match against prioritized classification rules
        for page_type, keywords in CLASSIFICATION_RULES:
            for kw in keywords:
                # Word boundary match in path or combined text
                pattern = rf"(?:\b|_|-){re.escape(kw)}(?:\b|_|-)"
                if re.search(pattern, combined_text) or kw in path:
                    return page_type

        return "OTHER"

    @classmethod
    def calculate_priority(
        cls,
        page_type: str,
        depth: int = 0,
        prioritize_contact: bool = True,
        prioritize_about: bool = True,
        prioritize_admissions: bool = False,
        prioritize_staff_management: bool = False,
    ) -> int:
        """Calculate queue priority weight (lower integer = higher priority in queue)."""
        base_priority = 5

        if page_type == "HOME":
            base_priority = 0
        elif page_type == "CONTACT" and prioritize_contact:
            base_priority = 1
        elif page_type == "ABOUT" and prioritize_about:
            base_priority = 2
        elif page_type == "ADMISSIONS" and prioritize_admissions:
            base_priority = 2
        elif page_type in ("PRINCIPAL", "MANAGEMENT", "FACULTY", "STAFF") and prioritize_staff_management:
            base_priority = 2
        elif page_type in ("LOCATION", "BRANCH"):
            base_priority = 3
        elif page_type == "INFRASTRUCTURE":
            base_priority = 4
        elif page_type in ("ABOUT", "CONTACT", "ADMISSIONS"):
            base_priority = 3

        # Depth adds penalty so shallower pages are generally explored earlier
        return base_priority * 10 + depth
