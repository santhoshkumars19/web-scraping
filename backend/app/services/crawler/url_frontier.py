"""
app/services/crawler/url_frontier.py

Priority queue managing URLs to crawl for a specific website.
Prioritizes high-value pages, tracks visited URLs to prevent loops,
and enforces crawl depth and max page limits.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from app.services.crawler.page_classifier import PageClassifier
from app.utils.url import normalize_url


@dataclass(order=True)
class FrontierItem:
    priority: int
    order: int
    depth: int = field(compare=False)
    url: str = field(compare=False)
    normalized_url: str = field(compare=False)
    page_type: str = field(compare=False)
    parent_url: str | None = field(default=None, compare=False)


class UrlFrontier:
    """Priority queue enforcing depth, page limits, and high-value URL ordering."""

    def __init__(
        self,
        max_pages: int = 15,
        max_depth: int = 2,
        prioritize_contact: bool = True,
        prioritize_about: bool = True,
        prioritize_admissions: bool = False,
        prioritize_staff_management: bool = False,
        max_frontier_urls: int | None = None,
    ) -> None:
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.prioritize_contact = prioritize_contact
        self.prioritize_about = prioritize_about
        self.prioritize_admissions = prioritize_admissions
        self.prioritize_staff_management = prioritize_staff_management
        from app.core.config import settings
        self.max_frontier_urls = (
            max_frontier_urls if max_frontier_urls is not None else settings.MAX_FRONTIER_URLS
        )

        self._queue: list[FrontierItem] = []
        self._enqueued: set[str] = set()
        self._visited: set[str] = set()
        self._order_counter: int = 0
        self.pages_crawled: int = 0

    def add(
        self,
        url: str,
        depth: int,
        tentative_type: str = "OTHER",
        parent_url: str | None = None,
    ) -> bool:
        """Add a URL to the queue if within limits and not already queued/visited."""
        if depth > self.max_depth:
            return False

        if len(self._enqueued) >= self.max_frontier_urls:
            return False

        try:
            norm_url = normalize_url(url)
        except Exception:
            return False

        if norm_url in self._visited or norm_url in self._enqueued:
            return False

        # Calculate priority
        priority = PageClassifier.calculate_priority(
            page_type=tentative_type,
            depth=depth,
            prioritize_contact=self.prioritize_contact,
            prioritize_about=self.prioritize_about,
            prioritize_admissions=self.prioritize_admissions,
            prioritize_staff_management=self.prioritize_staff_management,
        )

        item = FrontierItem(
            priority=priority,
            order=self._order_counter,
            depth=depth,
            url=url,
            normalized_url=norm_url,
            page_type=tentative_type,
            parent_url=parent_url,
        )
        self._order_counter += 1
        self._enqueued.add(norm_url)
        heapq.heappush(self._queue, item)
        return True

    def pop(self) -> FrontierItem | None:
        """Pop the highest priority item from the queue, if under page limit."""
        if self.is_finished():
            return None

        while self._queue:
            item = heapq.heappop(self._queue)
            if item.normalized_url not in self._visited:
                return item

        return None

    def mark_visited(self, normalized_url: str) -> None:
        """Mark a normalized URL as visited and increment the crawl counter."""
        self._visited.add(normalized_url)
        self.pages_crawled += 1

    def is_visited(self, normalized_url: str) -> bool:
        return normalized_url in self._visited

    def has_more(self) -> bool:
        return bool(self._queue) and self.pages_crawled < self.max_pages

    def is_finished(self) -> bool:
        return not bool(self._queue) or self.pages_crawled >= self.max_pages

    @property
    def total_enqueued(self) -> int:
        return len(self._enqueued)
