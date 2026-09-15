"""
app/services/discovery/fixture_provider.py

Deterministic development and test discovery provider using fictional data with reserved domains.
"""

from __future__ import annotations

import re

from app.schemas.discovery import DiscoveryCandidate
from app.services.discovery.base import DiscoveryProvider
from app.utils.url import extract_domain, normalize_url


# Curated realistic fictional candidate fixtures for key demo scenarios
FIXTURE_DATABASE: dict[tuple[str, str], list[dict]] = {
    ("cbse schools", "puducherry"): [
        {
            "name": "ABC International School",
            "url": "https://www.abcschool.example",
            "title": "ABC International School — CBSE Affiliated, Puducherry",
            "description": "Leading CBSE secondary educational institution in Puducherry.",
            "address": "12 Heritage Boulevard, White Town, Puducherry 605001",
            "phone": "+91 413 222 0001",
            "email": "info@abcschool.example",
        },
        {
            "name": "XYZ Model Senior Secondary School",
            "url": "https://xyzschool.example",
            "title": "XYZ Model School — Excellence in CBSE Education",
            "description": "Co-educational CBSE school serving students from KG to Grade 12 in Puducherry.",
            "address": "45 Mission Street, Puducherry 605001",
            "phone": "+91 413 222 0002",
            "email": "admissions@xyzschool.example",
        },
        {
            "name": "Puducherry Central Academy",
            "url": "https://puducherrycentral.example",
            "title": "Puducherry Central Academy CBSE",
            "description": "Established CBSE day school with STEM laboratory infrastructure.",
            "address": "78 Anna Salai, Puducherry 605002",
            "phone": "+91 413 222 0003",
            "email": "contact@puducherrycentral.example",
        },
        {
            "name": "Auroville Valley Global School",
            "url": "https://auroville-valley.example",
            "title": "Auroville Valley Global School (CBSE)",
            "description": "Holistic CBSE education integrated with progressive environmental programs.",
            "address": "Kuilapalayam Main Road, Near Puducherry",
            "phone": "+91 413 222 0004",
            "email": "office@auroville-valley.example",
        },
        {
            "name": "Seaside Scholars Academy",
            "url": "https://seasidescholars.example",
            "title": "Seaside Scholars Academy — Puducherry CBSE",
            "description": "Academic excellence and sports coaching for CBSE curriculum.",
            "address": "Beach Road, Puducherry 605001",
            "phone": "+91 413 222 0005",
            "email": "reach@seasidescholars.example",
        },
        {
            # Intentional duplicate candidate pointing to the same organization/domain to test deduplication!
            "name": "ABC International School (Official Portal)",
            "url": "https://abcschool.example/portal",
            "title": "ABC International School Online Portal",
            "description": "Student & Admissions portal for ABC International School.",
            "address": "12 Heritage Boulevard, White Town, Puducherry 605001",
            "phone": "+91 413 222 0001",
            "email": "info@abcschool.example",
        },
    ]
}


class FixtureDiscoveryProvider(DiscoveryProvider):
    """Provides deterministic, mock discovery data using standard reserved .example domains."""

    name = "fixture"

    async def search(
        self,
        *,
        keyword: str,
        location: str,
        limit: int = 50,
    ) -> list[DiscoveryCandidate]:
        kw_norm = keyword.strip().lower()
        loc_norm = location.strip().lower()

        # Check curated fixtures first
        items = FIXTURE_DATABASE.get((kw_norm, loc_norm))

        if not items:
            # Generate deterministic procedural candidates for any input
            base_kw = re.sub(r"[^a-zA-Z0-9]+", "", keyword.title()) or "Org"
            base_loc = re.sub(r"[^a-zA-Z0-9]+", "", location.title()) or "City"
            items = []
            for i in range(1, min(limit + 2, 8)):
                name = f"{base_loc} {base_kw} {i}"
                slug = f"{base_loc.lower()}-{base_kw.lower()}-{i}"
                domain = f"{slug}.example"
                url = f"https://www.{domain}"
                items.append({
                    "name": name,
                    "url": url,
                    "title": f"{name} — Official {keyword} in {location}",
                    "description": f"Comprehensive {keyword} provider located in {location}.",
                    "address": f"{i * 10} Main Street, {location}",
                    "phone": f"+91 98000 0000{i}",
                    "email": f"contact@{domain}",
                })

        candidates: list[DiscoveryCandidate] = []
        for item in items[:limit]:
            norm_url = normalize_url(item["url"])
            domain = extract_domain(norm_url)
            candidates.append(
                DiscoveryCandidate(
                    name=item["name"],
                    category=keyword,
                    location=location,
                    url=norm_url,
                    domain=domain,
                    source="FIXTURE",
                    source_url="fixture://local-dataset",
                    title=item.get("title"),
                    description=item.get("description"),
                    address=item.get("address"),
                    phone=item.get("phone"),
                    email=item.get("email"),
                    confidence=85.0,
                )
            )

        return candidates
