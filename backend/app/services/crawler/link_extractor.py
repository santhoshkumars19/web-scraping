"""
app/services/crawler/link_extractor.py

HTML link extractor using BeautifulSoup.
Resolves relative URLs, enforces domain boundaries, filters out asset links,
and extracts page title and anchor texts.
"""

from __future__ import annotations

import os
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from app.schemas.crawler import DiscoveredLink
from app.services.crawler.page_classifier import PageClassifier
from app.utils.url import extract_domain, normalize_url

IGNORED_EXTENSIONS = {
    # Images & icons
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff",
    # Documents & archives
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    # Media
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".webm",
    # Styles & scripts
    ".css", ".js", ".json", ".xml", ".rss",
}

IGNORED_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp", "sms", "whatsapp"}

SOCIAL_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "youtube.com", "pinterest.com", "tiktok.com", "reddit.com", "whatsapp.com",
    "telegram.me", "t.me", "github.com", "wikipedia.org", "google.com",
}


class LinkExtractor:
    """Extracts internal crawlable links and metadata from raw HTML."""

    @classmethod
    def extract_links(
        cls,
        html: str,
        base_url: str,
        website_domain: str,
        depth: int = 0,
        allow_subdomains: bool = False,
    ) -> tuple[str | None, list[DiscoveredLink]]:
        """Extract page title and internal links strictly within the website's domain boundaries.

        Args:
            html: Raw HTML string.
            base_url: The current page's URL for relative link resolution.
            website_domain: The allowed root domain (e.g. "abcschool.org").
            depth: Current page depth.
            allow_subdomains: Whether to allow crawling subdomains of website_domain.

        Returns:
            Tuple of (page_title, list of DiscoveredLink).
        """
        if not html:
            return None, []

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        # 1. Extract and sanitize page title
        page_title: str | None = None
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title_text = " ".join(title_tag.string.split())
            if title_text:
                page_title = title_text[:1024]

        # 2. Extract links
        discovered: list[DiscoveredLink] = []
        seen_urls: set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith("#"):
                continue

            # Parse scheme
            parsed_href = urlparse(raw_href)
            if parsed_href.scheme.lower() in IGNORED_SCHEMES:
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, raw_href)
            defragged_url, _ = urldefrag(absolute_url)

            # Check file extension
            parsed_target = urlparse(defragged_url)
            path_ext = os.path.splitext(parsed_target.path)[1].lower()
            if path_ext in IGNORED_EXTENSIONS:
                continue

            # Check domain boundary
            target_domain = extract_domain(defragged_url)
            if not target_domain:
                continue

            # Exclude known social / external domains
            if any(social in target_domain for social in SOCIAL_DOMAINS):
                continue

            if not cls._is_same_domain(target_domain, website_domain, allow_subdomains):
                continue

            # Normalize URL
            try:
                norm_url = normalize_url(defragged_url)
            except Exception:
                continue

            if norm_url in seen_urls:
                continue
            seen_urls.add(norm_url)

            anchor_text = " ".join(a_tag.get_text().split())[:200]
            tentative_type = PageClassifier.classify(norm_url, anchor_text=anchor_text)

            discovered.append(
                DiscoveredLink(
                    url=defragged_url,
                    normalized_url=norm_url,
                    anchor_text=anchor_text,
                    tentative_page_type=tentative_type,
                    depth=depth + 1,
                )
            )

        return page_title, discovered

    @staticmethod
    def _is_same_domain(target_domain: str, base_domain: str, allow_subdomains: bool) -> bool:
        """Check if target_domain belongs to base_domain."""
        target = target_domain.lower()
        base = base_domain.lower()

        if target == base:
            return True

        # Treat www.example.com and example.com as identical
        if target.replace("www.", "") == base.replace("www.", ""):
            return True

        if allow_subdomains:
            # Subdomain of base (e.g. portal.abcschool.org of abcschool.org)
            clean_base = base.replace("www.", "")
            if target.endswith(f".{clean_base}"):
                return True

        return False
