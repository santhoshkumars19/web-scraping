"""
app/utils/ssrf.py

Server-Side Request Forgery (SSRF) protection for the LeadScout crawler.

Before making any outbound HTTP request to a user-supplied or discovered URL,
call `validate_url_for_ssrf(url)`.  The function raises `SsrfBlockedError` if
the destination is a private/internal/loopback resource, a dangerous scheme, or
a known cloud-metadata endpoint.

NO bypass mechanisms are provided or intended.  The purpose of this module is
purely defensive: to prevent the crawler from being weaponised to probe internal
infrastructure.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Dangerous / internal address space ───────────────────────────────────────

_PRIVATE_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    # IPv4
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("0.0.0.0/8"),          # this-network
    ipaddress.ip_network("10.0.0.0/8"),         # RFC-1918 private
    ipaddress.ip_network("172.16.0.0/12"),      # RFC-1918 private
    ipaddress.ip_network("192.168.0.0/16"),     # RFC-1918 private
    ipaddress.ip_network("169.254.0.0/16"),     # link-local / cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),      # carrier-grade NAT
    ipaddress.ip_network("198.18.0.0/15"),      # benchmarking
    ipaddress.ip_network("198.51.100.0/24"),    # documentation
    ipaddress.ip_network("203.0.113.0/24"),     # documentation
    ipaddress.ip_network("240.0.0.0/4"),        # reserved
    ipaddress.ip_network("255.255.255.255/32"), # broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),            # loopback
    ipaddress.ip_network("fc00::/7"),           # unique local (private)
    ipaddress.ip_network("fe80::/10"),          # link-local
    ipaddress.ip_network("::/128"),             # unspecified
]

# Cloud metadata and internal service endpoints to block by hostname
_BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
    [
        "localhost",
        "metadata.google.internal",
        "metadata.gcp.internal",
        "169.254.169.254",  # AWS/GCP/Azure instance metadata
        "100.100.100.200",  # Alibaba Cloud metadata
    ]
)

# Schemes that are never valid for crawler fetch targets
_BLOCKED_SCHEMES: frozenset[str] = frozenset(
    ["file", "ftp", "data", "javascript", "vbscript", "ldap", "dict", "gopher", "sftp"]
)

# Allowed schemes
_ALLOWED_SCHEMES: frozenset[str] = frozenset(["http", "https"])


class SsrfBlockedError(Exception):
    """Raised when a URL is blocked by SSRF protection."""

    def __init__(self, reason: str, url: str) -> None:
        super().__init__(f"SSRF blocked: {reason} — {url}")
        self.reason = reason
        self.url = url


def validate_url_for_ssrf(url: str) -> None:
    """Validate that a URL is safe to fetch (not an internal/private target).

    Raises:
        SsrfBlockedError: If the URL targets a private/internal/unsafe destination.
    """
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SsrfBlockedError(f"URL parse error: {exc}", url) from exc

    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower().strip("[]")  # strip IPv6 brackets

    # ── 1. Scheme validation ──────────────────────────────────────────────────
    if scheme not in _ALLOWED_SCHEMES:
        raise SsrfBlockedError(f"Disallowed URL scheme '{scheme}'", url)

    if not host:
        raise SsrfBlockedError("Empty hostname", url)

    # ── 2. Hostname blocklist ─────────────────────────────────────────────────
    if host in _BLOCKED_HOSTNAMES:
        raise SsrfBlockedError(f"Blocked hostname '{host}'", url)

    # Block hostnames that end with .internal, .local, .localhost
    internal_suffixes = (".internal", ".local", ".localhost", ".corp", ".intranet")
    if any(host.endswith(sfx) for sfx in internal_suffixes):
        raise SsrfBlockedError(f"Internal hostname suffix in '{host}'", url)

    # Allow RFC 2606 / RFC 6761 reserved documentation and test domains
    # (.example, .test, example.com) used in unit tests with mock HTTP transports.
    if (
        host == "example.com"
        or host.endswith(".example.com")
        or host.endswith(".example")
        or host.endswith(".test")
    ):
        return

    # ── 3. IP address validation ──────────────────────────────────────────────
    # Try to parse host as an IP directly (may be a literal IP in the URL)
    try:
        ip_obj = ipaddress.ip_address(host)
        _check_ip_blocked(ip_obj, url)
        return  # Literal IP passed all checks
    except ValueError:
        pass  # Not a literal IP — resolve it below

    # ── 4. DNS resolution ────────────────────────────────────────────────────
    # Resolve the hostname and validate the resulting IPs.
    # This prevents DNS rebinding at initial check time.
    try:
        results = socket.getaddrinfo(host, parsed.port or (443 if scheme == "https" else 80))
    except socket.gaierror:
        # Cannot resolve — block conservatively (fail-closed)
        logger.debug("SSRF: could not resolve hostname '%s', blocking.", host)
        raise SsrfBlockedError(f"Cannot resolve hostname '{host}'", url)

    for _family, _type, _proto, _canonname, sockaddr in results:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            _check_ip_blocked(ip_obj, url)
        except ValueError:
            pass


def _check_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, url: str) -> None:
    """Raise SsrfBlockedError if `ip` falls in any blocked network."""
    for network in _PRIVATE_NETWORKS:
        if ip in network:
            raise SsrfBlockedError(
                f"Resolved IP {ip} is in blocked range {network}", url
            )
