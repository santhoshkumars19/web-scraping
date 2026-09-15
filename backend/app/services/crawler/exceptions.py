"""
app/services/crawler/exceptions.py

Exceptions raised during website crawling.
All crawler exceptions inherit from CrawlerError (and AppException).
"""

from __future__ import annotations

from app.core.exceptions import AppException


class CrawlerError(AppException):
    """Base exception for all crawler operations."""

    def __init__(
        self,
        message: str = "A crawler error occurred.",
        status_code: int = 400,
        code: str = "CRAWLER_ERROR",
        url: str | None = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, code=code)
        self.url = url


class InvalidURLError(CrawlerError):
    def __init__(self, message: str = "Invalid URL provided for crawling.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=400, code="INVALID_URL", url=url)


class DomainNotAllowedError(CrawlerError):
    def __init__(self, message: str = "URL target domain is outside the crawl scope.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=403, code="DOMAIN_NOT_ALLOWED", url=url)


class RobotsDisallowedError(CrawlerError):
    def __init__(self, message: str = "URL is disallowed by robots.txt.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=403, code="ROBOTS_DISALLOWED", url=url)


class AccessDeniedError(CrawlerError):
    def __init__(self, message: str = "Access denied (401/403).", status_code: int = 403, url: str | None = None) -> None:
        super().__init__(message=message, status_code=status_code, code="ACCESS_DENIED", url=url)


class FetchTimeoutError(CrawlerError):
    def __init__(self, message: str = "Request timed out during crawling.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=504, code="CRAWL_TIMEOUT", url=url)


class RateLimitedError(CrawlerError):
    def __init__(self, message: str = "Rate limited by target server (429).", url: str | None = None) -> None:
        super().__init__(message=message, status_code=429, code="RATE_LIMITED", url=url)


class ResponseTooLargeError(CrawlerError):
    def __init__(self, message: str = "Response payload exceeds maximum allowed size.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=413, code="RESPONSE_TOO_LARGE", url=url)


class NonHtmlContentError(CrawlerError):
    def __init__(self, message: str = "Content-Type is not HTML.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=415, code="NON_HTML_CONTENT", url=url)


class RedirectLimitError(CrawlerError):
    def __init__(self, message: str = "Too many redirects encountered.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=310, code="REDIRECT_LIMIT", url=url)


class CrawlDepthExceededError(CrawlerError):
    def __init__(self, message: str = "Maximum crawl depth exceeded.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=400, code="CRAWL_DEPTH_EXCEEDED", url=url)


class CrawlPageLimitReachedError(CrawlerError):
    def __init__(self, message: str = "Maximum pages per site limit reached.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=400, code="CRAWL_PAGE_LIMIT_REACHED", url=url)


class PlaywrightExecutionError(CrawlerError):
    def __init__(self, message: str = "Playwright browser execution failed.", url: str | None = None) -> None:
        super().__init__(message=message, status_code=500, code="PLAYWRIGHT_FAILED", url=url)
