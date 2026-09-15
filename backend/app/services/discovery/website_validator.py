"""
app/services/discovery/website_validator.py

Website reachability and validity check prior to registering official websites in LeadScout.
Performs URL normalization, SSRF checks, fake domain rejection, and a lightweight HTTP probe.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.core.logging import get_logger
from app.utils.ssrf import validate_url_for_ssrf, SsrfBlockedError
from app.utils.url import extract_domain, normalize_url

logger = get_logger(__name__)

# Reserved/fake domains that must NEVER be treated as real websites
DISALLOWED_DOMAIN_SUFFIXES = (
    ".example",
    ".invalid",
    ".test",
    ".localhost",
    ".local",
    ".internal",
    ".corp",
    ".onion",
)


@dataclass
class WebsiteReachabilityResult:
    """Outcome of validating a candidate website URL."""

    is_reachable: bool
    original_url: str
    normalized_url: str
    final_url: str | None = None
    http_status: int | None = None
    domain: str | None = None
    error: str | None = None


async def validate_website_reachability(
    url: str,
    *,
    timeout: float = 8.0,
    client: httpx.AsyncClient | None = None,
) -> WebsiteReachabilityResult:
    """Validate that a URL is a syntactically valid, safe, and reachable public website.

    Rules:
      1. Normalize URL and ensure http/https scheme.
      2. Strictly reject reserved/fictional domain extensions (.example, etc.).
      3. Verify against SSRF rules (disallow private IP subnets, metadata endpoints).
      4. Make a lightweight probe (HEAD with fallback to GET) to confirm the site responds.
      5. Capture and return the final redirected URL and HTTP status code.
    """
    raw_url = (url or "").strip()
    if not raw_url:
        return WebsiteReachabilityResult(
            is_reachable=False,
            original_url=raw_url,
            normalized_url="",
            error="Empty URL",
        )

    # 1. Ensure scheme
    if not raw_url.startswith(("http://", "https://")):
        raw_url = f"https://{raw_url}"

    # 2. Syntax & normalization
    try:
        norm_url = normalize_url(raw_url)
        domain = extract_domain(norm_url).lower()
    except Exception as exc:
        return WebsiteReachabilityResult(
            is_reachable=False,
            original_url=raw_url,
            normalized_url=raw_url,
            error=f"Invalid URL syntax: {exc}",
        )

    # 3. Reject fake / reserved / example domains
    if any(domain.endswith(sfx) or domain == sfx.lstrip(".") for sfx in DISALLOWED_DOMAIN_SUFFIXES):
        return WebsiteReachabilityResult(
            is_reachable=False,
            original_url=raw_url,
            normalized_url=norm_url,
            domain=domain,
            error=f"Disallowed domain suffix '{domain}' (fake/reserved domain)",
        )

    # 4. SSRF Validation
    try:
        validate_url_for_ssrf(norm_url)
    except SsrfBlockedError as exc:
        return WebsiteReachabilityResult(
            is_reachable=False,
            original_url=raw_url,
            normalized_url=norm_url,
            domain=domain,
            error=f"SSRF blocked: {exc.reason}",
        )
    except Exception as exc:
        return WebsiteReachabilityResult(
            is_reachable=False,
            original_url=raw_url,
            normalized_url=norm_url,
            domain=domain,
            error=f"Safety check error: {exc}",
        )

    # 5. Lightweight HTTP probe
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 LeadScoutBot/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async def _probe(c: httpx.AsyncClient) -> WebsiteReachabilityResult:
        try:
            # Try HEAD first for minimal overhead
            resp = await c.head(norm_url, headers=headers, follow_redirects=True, timeout=timeout)
            if resp.status_code in (405, 501, 403):
                # Many servers disallow HEAD or require GET for WAF/Cloudflare
                resp = await c.get(norm_url, headers=headers, follow_redirects=True, timeout=timeout)

            status = resp.status_code
            final_url = str(resp.url)
            final_norm = normalize_url(final_url)
            final_domain = extract_domain(final_norm).lower()

            # HTTP 200–399 are reachable. 403/401 is also reachable (server exists, protected/WAF)
            is_reachable = status < 500 or status in (401, 403)
            return WebsiteReachabilityResult(
                is_reachable=is_reachable,
                original_url=raw_url,
                normalized_url=norm_url,
                final_url=final_url,
                http_status=status,
                domain=final_domain or domain,
                error=None if is_reachable else f"HTTP error {status}",
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            return WebsiteReachabilityResult(
                is_reachable=False,
                original_url=raw_url,
                normalized_url=norm_url,
                domain=domain,
                error=f"Connection failed: {e}",
            )
        except Exception as e:
            return WebsiteReachabilityResult(
                is_reachable=False,
                original_url=raw_url,
                normalized_url=norm_url,
                domain=domain,
                error=str(e),
            )

    if client is not None:
        return await _probe(client)

    async with httpx.AsyncClient(timeout=timeout, verify=False) as probe_client:
        return await _probe(probe_client)
