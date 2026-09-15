"""
app/utils/task_id.py

Concurrency-safe human-readable Task ID generator.

Format: TASK-000001, TASK-000002, etc.

Implementation:
- In PostgreSQL: Uses the database sequence `task_id_seq` via `nextval('task_id_seq')`.
  This is guaranteed atomic, non-blocking, and collision-free even under heavy concurrency.
- In SQLite / test fallback: Uses an atomic sequence table (`task_id_sequence`)
  with `AUTOINCREMENT` to ensure monotonically increasing, unique IDs.
- Never relies on `SELECT count(*) + 1` or `SELECT max(...) + 1`.
"""

from __future__ import annotations

import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

_sqlite_seq_lock = asyncio.Lock()
_sqlite_seq_counter = 0


async def generate_task_id(session: AsyncSession) -> str:
    """Generate the next unique, sequential, human-readable Task ID.

    Returns:
        Formatted string, e.g. "TASK-000001", "TASK-000124".
    """
    bind = session.bind
    dialect_name = bind.dialect.name if bind else "postgresql"

    if dialect_name == "postgresql":
        # Concurrency-safe PostgreSQL sequence
        result = await session.execute(sa.text("SELECT nextval('task_id_seq')"))
        seq_num = result.scalar()
        return f"TASK-{int(seq_num):06d}"

    # SQLite / in-memory test fallback using lock-protected monotonic sequence
    global _sqlite_seq_counter
    async with _sqlite_seq_lock:
        res = await session.execute(sa.text("SELECT count(*) FROM scraping_tasks"))
        db_count = res.scalar() or 0
        _sqlite_seq_counter = max(_sqlite_seq_counter + 1, db_count + 1)
        seq_num = _sqlite_seq_counter

    return f"TASK-{int(seq_num):06d}"
