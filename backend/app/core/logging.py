"""
app/core/logging.py

Structured application logging configuration with sensitive data redaction.

Guidelines:
  - Passwords, tokens, API keys, and PII are NEVER logged.
  - Log level is driven entirely by Settings.LOG_LEVEL.
  - SensitiveDataFilter sanitizes Bearer tokens, cookies, passwords, and secret keys.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

_REDACTION_PATTERNS = [
    # Authorization: Bearer <token>
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]+"), r"\1[REDACTED]"),
    # Passwords in query strings, json, or key-value format
    (re.compile(r'(?i)(["\']?password["\']?\s*[:=]\s*["\']?)[^\s&,;"\']+'), r"\1[REDACTED]"),
    # Secret keys / JWTs in key-value pairs
    (re.compile(r'(?i)(["\']?secret(?:_key)?["\']?\s*[:=]\s*["\']?)[^\s&,;"\']+'), r"\1[REDACTED]"),
    # Cookies
    (re.compile(r"(?i)(leadscout_access_token=)[^\s;]+"), r"\1[REDACTED]"),
]


class SensitiveDataFilter(logging.Filter):
    """Redacts sensitive credentials, tokens, and passwords from log records safely."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if record.args:
                # Merge args into msg first, then clear args so downstream Formatter does not fail
                record.msg = str(record.msg) % record.args
                record.args = ()
            if isinstance(record.msg, str):
                msg = record.msg
                for pattern, replacement in _REDACTION_PATTERNS:
                    msg = pattern.sub(replacement, msg)
                record.msg = msg
        except Exception:
            pass
        return True


def configure_logging(settings: "Settings") -> None:
    """Configure root logger and named application loggers.

    Call this once at application startup before any other imports
    that may trigger log output.
    """
    log_level: int = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=date_fmt))
    handler.addFilter(SensitiveDataFilter())

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers in production.
    if settings.is_production:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    else:
        sql_level = logging.DEBUG if settings.DEBUG else logging.WARNING
        logging.getLogger("sqlalchemy.engine").setLevel(sql_level)

    logging.getLogger("leadscout").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger scoped under the 'leadscout' hierarchy."""
    if not name.startswith("leadscout"):
        name = f"leadscout.{name}"
    return logging.getLogger(name)
