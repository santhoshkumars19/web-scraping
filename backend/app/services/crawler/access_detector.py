"""
app/services/crawler/access_detector.py

Detects access controls, CAPTCHAs, bot challenges, paywalls, and login walls.
Strictly informs the crawler to STOP crawling restricted paths or sites.
DOES NOT implement or permit bypass mechanisms.
"""

from __future__ import annotations

import enum
import re
from typing import Tuple
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AccessStatus(str, enum.Enum):
    ALLOWED = "ALLOWED"
    ACCESS_DENIED = "ACCESS_DENIED"
    CAPTCHA_BLOCKED = "CAPTCHA_BLOCKED"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    PAYWALL_BLOCKED = "PAYWALL_BLOCKED"


# Obvious CAPTCHA and anti-bot challenge indicators (case-insensitive)
_CAPTCHA_PATTERNS = [
    r"verify you are human",
    r"verify that you are human",
    r"please complete the security check",
    r"attention required!?\s*\|\s*cloudflare",
    r"checking your browser before accessing",
    r"ddos-guard",
    r"robot check",
    r"cf-browser-verification",
    r"g-recaptcha",
    r"hcaptcha",
    r"cf-turnstile",
    r"are you a human",
    r"security challenge",
]

# Login wall paths and indicators
_LOGIN_PATH_KEYWORDS = {"login", "signin", "sign-in", "authenticate", "auth"}
_LOGIN_TEXT_PATTERNS = [
    r"please sign in to continue",
    r"please log in to continue",
    r"sign in to your account",
]

# Paywall indicators
_PAYWALL_PATTERNS = [
    r"this content is for subscribers only",
    r"subscribe to continue reading",
    r"subscription required",
    r"you have reached your free article limit",
    r"exclusive for premium members",
]


class AccessDetector:
    """Evaluates HTTP response status and content to detect access controls."""

    @classmethod
    def check(
        cls,
        status_code: int,
        html: str,
        final_url: str,
        headers: dict[str, str] | None = None,
    ) -> Tuple[AccessStatus, str | None]:
        """Inspect a response for access control, challenge walls, or restrictions.

        Returns:
            (AccessStatus, reason_str | None)
        """
        # 1. HTTP Status Code Checks
        if status_code in (401, 403):
            return AccessStatus.ACCESS_DENIED, f"HTTP {status_code} Access Denied"

        if status_code == 429:
            return AccessStatus.ACCESS_DENIED, "HTTP 429 Rate Limited"

        lower_html = (html or "").lower()

        # 2. CAPTCHA / Bot Challenge Detection
        for pattern in _CAPTCHA_PATTERNS:
            if re.search(pattern, lower_html):
                logger.info("CAPTCHA / challenge pattern '%s' detected at %s", pattern, final_url)
                return AccessStatus.CAPTCHA_BLOCKED, f"CAPTCHA or challenge detected: '{pattern}'"

        # Check headers if provided (e.g. Cloudflare CF-Chl-Bypass or challenge)
        if headers:
            for k, v in headers.items():
                if "cf-mitigated" in k.lower() or "challenge" in v.lower():
                    return AccessStatus.CAPTCHA_BLOCKED, "Challenge header detected"

        # 3. Login Wall Detection
        parsed = urlparse(final_url)
        path_parts = [p.lower() for p in parsed.path.strip("/").split("/") if p]
        if any(part in _LOGIN_PATH_KEYWORDS for part in path_parts):
            logger.info("Login wall detected by URL path '%s' at %s", parsed.path, final_url)
            return AccessStatus.LOGIN_REQUIRED, f"Login redirect: {parsed.path}"

        for pattern in _LOGIN_TEXT_PATTERNS:
            if re.search(pattern, lower_html):
                logger.info("Login required text pattern detected at %s", final_url)
                return AccessStatus.LOGIN_REQUIRED, "Login required to view content"

        # 4. Paywall Detection
        for pattern in _PAYWALL_PATTERNS:
            if re.search(pattern, lower_html):
                logger.info("Paywall detected at %s", final_url)
                return AccessStatus.PAYWALL_BLOCKED, "Content is behind a paywall"

        return AccessStatus.ALLOWED, None
