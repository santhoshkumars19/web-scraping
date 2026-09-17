"""
app/utils/ssrf.py

Server-Side Request Forgery (SSRF) protection for the LeadScout crawler.

Before making any outbound HTTP request to a user-supplied or discovered URL,
call `validate_url_for_ssrf(url)` or `validate_url_for_ssrf_async(url)`. The function
raises `SsrfBlockedError` if the destination is a private/internal/loopback resource,
a dangerous scheme, or a known cloud-metadata endpoint.

DNS resolution is bounded by an explicit timeout (default 3.0s) and executed
in a non-blocking threadpool/executor so as never to block the main event loop
or Celery worker.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import ipaddress
import socket
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Dangerous / internal address space ───────────────────────────────────────

_PRIVATE_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    # IPv4
    ipaddress.ip_network("127.0.0.0/8"),        # loopback
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


def _parse_and_validate_base(url: str) -> tuple[str, str, int]:
    """Perform scheme, host, and domain blocklist checks prior to DNS resolution."""
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SsrfBlockedError(f"URL parse error: {exc}", url) from exc

    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower().strip("[]")  # strip IPv6 brackets

    if scheme not in _ALLOWED_SCHEMES:
        raise SsrfBlockedError(f"Disallowed URL scheme '{scheme}'", url)

    if not host:
        raise SsrfBlockedError("Empty hostname", url)

    if host in _BLOCKED_HOSTNAMES:
        raise SsrfBlockedError(f"Blocked hostname '{host}'", url)

    internal_suffixes = (".internal", ".local", ".localhost", ".corp", ".intranet")
    if any(host.endswith(sfx) for sfx in internal_suffixes):
        raise SsrfBlockedError(f"Internal hostname suffix in '{host}'", url)

    port = parsed.port or (443 if scheme == "https" else 80)
    return scheme, host, port


def _is_test_domain(host: str) -> bool:
    return (
        host == "example.com"
        or host.endswith(".example.com")
        or host.endswith(".example")
        or host.endswith(".test")
    )


async def validate_url_for_ssrf_async(
    url: str,
    dns_timeout: float = 3.0,
    task_id: str | None = None,
) -> None:
    """Validate that a URL is safe to fetch using bounded non-blocking DNS resolution.

    Raises:
        SsrfBlockedError: If the URL targets a private/internal/unsafe destination or DNS times out.
    """
    scheme, host, port = _parse_and_validate_base(url)

    if _is_test_domain(host):
        return

    try:
        ip_obj = ipaddress.ip_address(host)
        _check_ip_blocked(ip_obj, url)
        return
    except ValueError:
        pass

    tid_str = f"[{task_id}] " if task_id else ""
    logger.info("%sdns_validation_started: host=%s", tid_str, host)

    try:
        loop = asyncio.get_running_loop()
        results = await asyncio.wait_for(
            loop.getaddrinfo(host, port),
            timeout=dns_timeout,
        )
        logger.info("%sdns_validation_completed: host=%s", tid_str, host)
    except asyncio.TimeoutError:
        logger.warning(
            "%sdns_validation_completed: DNS resolution timed out for host '%s' (timeout=%.1fs)",
            tid_str,
            host,
            dns_timeout,
        )
        raise SsrfBlockedError(f"DNS resolution timed out for '{host}'", url)
    except socket.gaierror:
        logger.debug("%sdns_validation_completed: could not resolve host '%s'", tid_str, host)
        raise SsrfBlockedError(f"Cannot resolve hostname '{host}'", url)
    except Exception as exc:
        logger.debug("%sdns_validation_completed: DNS resolution error for host '%s': %s", tid_str, host, exc)
        raise SsrfBlockedError(f"DNS resolution error for '{host}': {exc}", url)

    for _family, _type, _proto, _canonname, sockaddr in results:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            _check_ip_blocked(ip_obj, url)
        except ValueError:
            pass


def validate_url_for_ssrf(
    url: str,
    dns_timeout: float = 3.0,
    task_id: str | None = None,
) -> None:
    """Synchronous SSRF validation with bounded DNS resolution.

    Safe for synchronous callers. Bounds getaddrinfo with ThreadPoolExecutor timeout.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If called inside an async loop, execute async validator safely
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(asyncio.run, validate_url_for_ssrf_async(url, dns_timeout, task_id)).result()
            return

    scheme, host, port = _parse_and_validate_base(url)

    if _is_test_domain(host):
        return

    try:
        ip_obj = ipaddress.ip_address(host)
        _check_ip_blocked(ip_obj, url)
        return
    except ValueError:
        pass

    tid_str = f"[{task_id}] " if task_id else ""
    logger.info("%sdns_validation_started: host=%s", tid_str, host)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(socket.getaddrinfo, host, port)
        try:
            results = future.result(timeout=dns_timeout)
            logger.info("%sdns_validation_completed: host=%s", tid_str, host)
        except concurrent.futures.TimeoutError:
            logger.warning(
                "%sdns_validation_completed: DNS resolution timed out for host '%s'",
                tid_str,
                host,
            )
            raise SsrfBlockedError(f"DNS resolution timed out for '{host}'", url)
        except socket.gaierror:
            logger.debug("%sdns_validation_completed: could not resolve host '%s'", tid_str, host)
            raise SsrfBlockedError(f"Cannot resolve hostname '{host}'", url)
        except Exception as exc:
            logger.debug("%sdns_validation_completed: DNS resolution error for host '%s': %s", tid_str, host, exc)
            raise SsrfBlockedError(f"DNS resolution error for '{host}': {exc}", url)

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
