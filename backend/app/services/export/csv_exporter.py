"""
app/services/export/csv_exporter.py

CSV generation and streaming utilities using Python's standard csv.writer.
Ensures UTF-8 encoding with BOM, safe escaping of quotes/commas/newlines,
and memory-safe chunked generation.
"""

from __future__ import annotations

import csv
import io
from typing import Iterator, Sequence


def generate_csv_bytes(
    headers: list[str],
    rows: Sequence[dict[str, str]],
) -> bytes:
    """Generate complete CSV file content as UTF-8 encoded bytes with BOM.

    BOM (\\ufeff) ensures Microsoft Excel and spreadsheet programs automatically
    recognize UTF-8 characters without manual import encoding configuration.
    """
    output = io.StringIO()
    # UTF-8 BOM
    output.write("\ufeff")

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(headers)

    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])

    return output.getvalue().encode("utf-8")


def iter_csv_chunks(
    headers: list[str],
    rows: Sequence[dict[str, str]],
    chunk_size: int = 100,
) -> Iterator[bytes]:
    """Generator yielding CSV data in byte chunks for FastAPI StreamingResponse.

    Avoids creating one massive string in memory when streaming thousands of rows.
    """
    # 1. Emit BOM and header row
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(headers)
    yield output.getvalue().encode("utf-8")

    output.seek(0)
    output.truncate(0)

    # 2. Emit rows in batches
    batch_count = 0
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
        batch_count += 1
        if batch_count >= chunk_size:
            yield output.getvalue().encode("utf-8")
            output.seek(0)
            output.truncate(0)
            batch_count = 0

    # Emit any remaining buffer
    remaining = output.getvalue()
    if remaining:
        yield remaining.encode("utf-8")
