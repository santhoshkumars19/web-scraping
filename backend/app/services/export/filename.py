"""
app/services/export/filename.py

Safe filename generation and sanitization for Lead exports.
Guards against path traversal, control characters, and illegal filesystem characters.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone


def sanitize_filename(name: str, max_length: int = 64) -> str:
    """Sanitize a string for safe usage in Content-Disposition and filenames.

    Removes directory traversal sequences, slashes, colons, quotes, control
    characters, and trims length.
    """
    if not name or not name.strip():
        return "export"

    # Normalize unicode (NFKD)
    normalized = unicodedata.normalize("NFKD", name.strip())

    # Replace any non-alphanumeric chars with hyphen
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", normalized)

    # Collapse repeated hyphens
    clean = re.sub(r"-{2,}", "-", clean)

    # Strip leading/trailing hyphens
    clean = clean.strip("-")

    if not clean:
        clean = "export"

    return clean[:max_length]


def build_export_filename(
    source_type: str,
    *,
    task_id: str | None = None,
    lead_name: str | None = None,
    extension: str = "csv",
    custom_name: str | None = None,
) -> str:
    """Construct a clean, predictable filename with timestamp.

    Examples:
      - task: leadscout-task-TASK-000124-2026-09-12.csv
      - single lead: leadscout-st-patrick-school-2026-09-12.xlsx
      - selected: leadscout-selected-leads-2026-09-12.csv
      - all / filtered: leadscout-leads-2026-09-12.xlsx
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ext = extension.lstrip(".").lower()

    if custom_name and custom_name.strip():
        base = sanitize_filename(custom_name)
        # Avoid double date if user already included it
        if today_str not in base:
            return f"{base}-{today_str}.{ext}"
        return f"{base}.{ext}"

    st = source_type.lower()
    if st == "task" and task_id:
        clean_task = sanitize_filename(task_id)
        return f"leadscout-task-{clean_task}-{today_str}.{ext}"

    if st == "single_lead" and lead_name:
        clean_lead = sanitize_filename(lead_name)
        return f"leadscout-{clean_lead}-{today_str}.{ext}"

    if st == "selected":
        return f"leadscout-selected-leads-{today_str}.{ext}"

    return f"leadscout-leads-{today_str}.{ext}"
