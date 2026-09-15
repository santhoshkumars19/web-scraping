"""
app/services/crawler/playwright_crawler.py

Level 2 headless browser crawler using Playwright.
Invoked strictly as a fallback when Level 1 detects a client-side JavaScript shell.
Includes graceful degradation if browser binaries are not installed.
"""

from __future__ import annotations

import re
import time
from typing import Any

from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SPA_SHELL_PATTERNS = [
    r'<div\s+id=["\'](?:root|app|__next|application)["\']\s*>\s*</div>',
    r'<noscript>.*?(?:enable javascript|requires javascript|javascript to be enabled).*?</noscript>',
]


class PlaywrightCrawler:
    """Level 2 browser crawler for JavaScript-heavy client-side applications."""

    def __init__(
        self,
        enabled: bool | None = None,
        timeout: float | None = None,
    ) -> None:
        self.enabled = settings.PLAYWRIGHT_ENABLED if enabled is None else enabled
        self.timeout = timeout or settings.PLAYWRIGHT_TIMEOUT_SECONDS

    @classmethod
    def is_js_shell(cls, html: str, internal_links_count: int = 0) -> bool:
        """Heuristic check to determine whether the page is an unhydrated JS shell."""
        if not html:
            return True

        # If we already found internal links, it's rarely an empty shell
        if internal_links_count > 2:
            return False

        lower_html = html.lower()

        # Check for SPA markers
        for pattern in SPA_SHELL_PATTERNS:
            if re.search(pattern, lower_html, re.IGNORECASE | re.DOTALL):
                return True

        # Check visible text length
        try:
            soup = BeautifulSoup(html, "html.parser")
            for element in soup(["script", "style", "meta", "noscript"]):
                element.decompose()
            visible_text = " ".join(soup.stripped_strings)
            # If visible text is very sparse and no links found
            if len(visible_text) < 120 and internal_links_count == 0:
                return True
        except Exception:
            pass

        return False

    async def fetch_rendered(
        self,
        url: str,
    ) -> tuple[str, str, int, float] | None:
        """Fetch page using headless Chromium to execute JavaScript.

        Returns:
            Tuple of (rendered_html, final_url, status_code, elapsed_ms)
            or None if Playwright is disabled / fails to run.
        """
        if not self.enabled:
            return None

        start_time = time.monotonic()

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright is not installed in the python environment.")
            return None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
                context = await browser.new_context(
                    user_agent=settings.CRAWLER_USER_AGENT,
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()

                timeout_ms = int(self.timeout * 1000)
                page.set_default_navigation_timeout(timeout_ms)

                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                # Wait briefly for client-side rendering / hydration
                try:
                    await page.wait_for_load_state("networkidle", timeout=3000)
                except Exception:
                    pass  # Network idle timeout is non-fatal

                final_url = page.url
                status_code = response.status if response else 200
                rendered_html = await page.content()

                await context.close()
                await browser.close()

                elapsed_ms = (time.monotonic() - start_time) * 1000.0
                return rendered_html, final_url, status_code, elapsed_ms

        except Exception as e:
            logger.warning(
                "Playwright execution failed for %s: %s. Falling back to Level 1 response.",
                url,
                e,
            )
            return None
