"""
app/services/discovery/public_search.py

Live public-web discovery provider combining OpenStreetMap Nominatim POI search
and DuckDuckGo public search. Returns real organizations, genuine addresses,
and verified candidate URLs without requiring paid APIs or CAPTCHA bypass.
"""

from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup
import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.discovery import DiscoveryCandidate
from app.services.discovery.base import DiscoveryProvider
from app.services.discovery.normalizer import (
    normalize_location_text,
    normalize_organization_name,
)
from app.services.discovery.query_builder import build_discovery_queries
from app.services.discovery.ranking import (
    DIRECTORY_DOMAINS,
    is_candidate_official_website,
    score_candidate,
)
from app.services.discovery.website_validator import validate_website_reachability
from app.utils.url import extract_domain, normalize_url

logger = get_logger(__name__)

# Search engines and directories to exclude from candidate official websites
AGGREGATOR_DOMAINS = DIRECTORY_DOMAINS | {
    "tripadvisor.com",
    "tripadvisor.in",
    "zomato.com",
    "swiggy.com",
    "yelp.com",
    "makemytrip.com",
    "goibibo.com",
    "booking.com",
    "agoda.com",
    "trivago.com",
    "trivago.in",
    "expedia.com",
    "holidify.com",
    "thrillophilia.com",
    "whatshot.in",
    "lbb.in",
    "magicpin.in",
    "dineout.co.in",
    "eatsure.com",
    "nearbuy.com",
    "mapsofindia.com",
    "wikitravel.org",
    "wikivoyage.org",
    "duckduckgo.com",
    "bing.com",
    "google.com",
    "yahoo.com",
}


class PublicSearchProvider(DiscoveryProvider):
    """Live public web discovery provider.

    Discovers real public businesses and official websites from:
      1. OpenStreetMap Nominatim API (public POI directory)
      2. DuckDuckGo public HTML/Lite search (organic web results)
    """

    name = "public_search"

    def __init__(
        self,
        *,
        enabled: bool = True,
        timeout_seconds: float = 12.0,
        max_retries: int = 2,
    ) -> None:
        self.enabled = enabled
        self.timeout_seconds = getattr(settings, "PUBLIC_SEARCH_TIMEOUT_SECONDS", timeout_seconds)
        self.max_retries = getattr(settings, "PUBLIC_SEARCH_MAX_RETRIES", max_retries)

    async def is_available(self) -> bool:
        return self.enabled

    async def search(
        self,
        *,
        keyword: str,
        location: str,
        limit: int = 50,
    ) -> list[DiscoveryCandidate]:
        """Execute public web discovery for keyword and location."""
        if not self.enabled:
            logger.info("PublicSearchProvider is disabled; skipping external search.")
            return []

        clean_kw = keyword.strip()
        clean_loc = location.strip()
        if not clean_kw and not clean_loc:
            return []

        candidates: list[DiscoveryCandidate] = []
        seen_keys: set[str] = set()

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 LeadScoutBot/1.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=self.timeout_seconds,
            follow_redirects=True,
            verify=False,
        ) as client:
            # ── 1. Strategy A: OpenStreetMap Nominatim POI Search ─────────────
            osm_candidates = await self._search_nominatim(
                client=client,
                keyword=clean_kw,
                location=clean_loc,
                limit=limit,
            )

            for cand in osm_candidates:
                key = f"{cand.name.lower()}:{cand.domain or ''}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidates.append(cand)

            # ── 2. Strategy B: DuckDuckGo Public Organic Search ──────────────
            # Run if we still need more candidates or want to enrich with web results
            ddg_limit = max(5, limit - len(candidates))
            if ddg_limit > 0:
                ddg_candidates = await self._search_duckduckgo(
                    client=client,
                    keyword=clean_kw,
                    location=clean_loc,
                    limit=ddg_limit,
                )

                for cand in ddg_candidates:
                    key = f"{cand.name.lower()}:{cand.domain or ''}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        candidates.append(cand)

            # ── 3. Complementary Official Website Resolution ───────────────────
            # For Nominatim candidates lacking a website, do a targeted search
            candidates_to_resolve = [c for c in candidates if not c.url or c.url.startswith("https://www.openstreetmap.org")]
            for cand in candidates_to_resolve[:min(limit, 8)]:
                official_url = await self._resolve_official_website(
                    client=client,
                    org_name=cand.name,
                    location=clean_loc,
                )
                if official_url:
                    cand.url = official_url
                    cand.domain = extract_domain(official_url)
                    cand.is_official_candidate = True

        logger.info("PublicSearchProvider discovered %d total candidates for '%s' in '%s'", len(candidates), clean_kw, clean_loc)
        return candidates[:limit]

    # ── Strategy A: OpenStreetMap Nominatim ────────────────────────────────────

    async def _search_nominatim(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        location: str,
        limit: int,
    ) -> list[DiscoveryCandidate]:
        """Query Nominatim for real public POI places and addresses."""
        query = f"{keyword} in {location}"
        candidates: list[DiscoveryCandidate] = []

        try:
            logger.info("Nominatim search: '%s'", query)
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "addressdetails": "1",
                    "extratags": "1",
                    "limit": str(min(limit, 50)),
                },
                headers={"User-Agent": "LeadScout/1.0 (+https://leadscout.example; discovery-bot)"},
            )

            if resp.status_code != 200:
                logger.warning("Nominatim HTTP %s for query '%s'", resp.status_code, query)
                return []

            items = resp.json()
            if not isinstance(items, list):
                return []

            for item in items:
                raw_name = item.get("name") or (item.get("display_name", "").split(",")[0])
                clean_name = normalize_organization_name(raw_name)
                if not clean_name or len(clean_name) < 2:
                    continue

                # Build clean address
                addr_dict = item.get("address") or {}
                addr_parts = []
                for field in ("road", "suburb", "neighbourhood", "town", "city", "state", "postcode"):
                    val = addr_dict.get(field)
                    if val and val not in addr_parts:
                        addr_parts.append(val)

                real_address = ", ".join(addr_parts) if addr_parts else item.get("display_name")
                # Normalize address to remove trailing country if present
                if real_address:
                    real_address = re.sub(r",\s*India\s*$", "", real_address, flags=re.IGNORECASE).strip()

                ext = item.get("extratags") or {}
                raw_website = ext.get("website") or ext.get("contact:website")
                raw_phone = ext.get("phone") or ext.get("contact:phone")
                raw_email = ext.get("email") or ext.get("contact:email")

                site_url = ""
                domain = ""
                is_official = False

                if raw_website:
                    try:
                        norm_site = normalize_url(raw_website)
                        site_domain = extract_domain(norm_site).lower()
                        if not any(d in site_domain for d in AGGREGATOR_DOMAINS):
                            site_url = norm_site
                            domain = site_domain
                            is_official = True
                    except Exception:
                        pass

                cand_url = site_url or f"https://www.openstreetmap.org/search?query={urllib.parse.quote(raw_name)}"
                cand_domain = domain or extract_domain(cand_url) or "openstreetmap.org"

                cand = DiscoveryCandidate(
                    name=clean_name,
                    category=keyword,
                    location=location,
                    url=cand_url,
                    domain=cand_domain,
                    source="PUBLIC_SEARCH",
                    source_url=f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}",
                    title=item.get("display_name"),
                    description=f"Public {keyword} entity verified in {location}.",
                    address=real_address or None,
                    phone=raw_phone or None,
                    email=raw_email or None,
                    confidence=85.0 if is_official else 75.0,
                    is_official_candidate=is_official,
                )
                candidates.append(cand)

        except Exception as exc:
            logger.warning("Nominatim query failed: %s", exc)

        return candidates

    # ── Strategy B: DuckDuckGo Public Search ───────────────────────────────────

    async def _search_duckduckgo(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        location: str,
        limit: int,
    ) -> list[DiscoveryCandidate]:
        """Search DuckDuckGo HTML for organic business and website results."""
        queries = build_discovery_queries(keyword, location)
        candidates: list[DiscoveryCandidate] = []
        seen_domains: set[str] = set()

        for q in queries[:2]:
            try:
                logger.info("DuckDuckGo HTML search: '%s'", q)
                resp = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": q},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                results = soup.select(".result")

                for res in results:
                    title_elem = res.select_one(".result__title a")
                    snippet_elem = res.select_one(".result__snippet")
                    if not title_elem:
                        continue

                    raw_title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "").strip()

                    # Unwrap DDG redirect parameter (uddg)
                    target_url = self._unwrap_ddg_url(href)
                    if not target_url or not target_url.startswith(("http://", "https://")):
                        continue

                    try:
                        norm_url = normalize_url(target_url)
                        domain = extract_domain(norm_url).lower()
                    except Exception:
                        continue

                    # Filter out directories, search engines, and fake domains
                    if any(d in domain for d in AGREGATOR_DOMAINS) or domain.endswith((".example", ".invalid", ".test")):
                        continue

                    if domain in seen_domains:
                        continue
                    seen_domains.add(domain)

                    # Extract clean organization name from title
                    clean_name = self._extract_name_from_title(raw_title, location, keyword)
                    if not clean_name or len(clean_name) < 2:
                        continue

                    cand = DiscoveryCandidate(
                        name=clean_name,
                        category=keyword,
                        location=location,
                        url=norm_url,
                        domain=domain,
                        source="PUBLIC_SEARCH",
                        source_url=f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}",
                        title=raw_title,
                        description=snippet_elem.get_text(strip=True) if snippet_elem else None,
                        confidence=70.0,
                        is_official_candidate=True,
                    )
                    candidates.append(cand)
                    if len(candidates) >= limit:
                        break

            except Exception as exc:
                logger.warning("DuckDuckGo query '%s' failed: %s", q, exc)

            if len(candidates) >= limit:
                break

        return candidates

    # ── Strategy C: Targeted Official Website Search ───────────────────────────

    async def _resolve_official_website(
        self,
        client: httpx.AsyncClient,
        org_name: str,
        location: str,
    ) -> str | None:
        """Perform a targeted search to find an organization's official website."""
        query = f'"{org_name}" "{location}" official website'
        try:
            resp = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.select(".result__title a")
            for a in results:
                href = a.get("href", "").strip()
                target_url = self._unwrap_ddg_url(href)
                if not target_url or not target_url.startswith(("http://", "https://")):
                    continue

                try:
                    norm_url = normalize_url(target_url)
                    domain = extract_domain(norm_url).lower()
                except Exception:
                    continue

                if any(d in domain for d in AGREGATOR_DOMAINS) or domain.endswith((".example", ".invalid", ".test")):
                    continue

                # Lightweight probe to confirm it is reachable
                reachability = await validate_website_reachability(norm_url, timeout=5.0, client=client)
                if reachability.is_reachable:
                    return reachability.final_url or reachability.normalized_url

        except Exception as exc:
            logger.debug("Failed to resolve official site for '%s': %s", org_name, exc)

        return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _unwrap_ddg_url(href: str) -> str:
        """Unwrap DDG redirect target from /l/?uddg=... or return href directly."""
        if "uddg=" in href:
            parsed = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed.query)
            target = query_params.get("uddg", [""])[0]
            if target:
                return target
        if href.startswith(("http://", "https://")):
            return href
        return ""

    @staticmethod
    def _extract_name_from_title(title: str, location: str, keyword: str) -> str:
        """Extract a clean organization name from an HTML title."""
        # Strip common trailing suffixes
        t = re.split(r"[-|:–—·•]", title)[0].strip()
        # Strip words like 'Official Website', 'Home', etc.
        t = re.sub(r"(?i)\b(official website|official site|home page|home|welcome to)\b", "", t).strip()
        # Normalize
        clean = normalize_organization_name(t)
        return clean
