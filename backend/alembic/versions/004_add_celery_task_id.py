"""004_add_celery_task_id

Revision ID: 004_add_celery_task_id
Revises: 003_add_lead_verification_scoring_and_metrics
Create Date: 2026-09-12 14:00:00.000000+00:00

Adds celery_task_id column and index to scraping_tasks table.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_add_celery_task_id"
down_revision: Union[str, None] = "003_add_lead_verification_scoring_and_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scraping_tasks",
        sa.Column("celery_task_id", sa.String(255), nullable=True),
    )
    op.create_index(
        op.f("ix_scraping_tasks_celery_task_id"),
        "scraping_tasks",
        ["celery_task_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_scraping_tasks_celery_task_id"),
        table_name="scraping_tasks",
    )
    op.drop_column("scraping_tasks", "celery_task_id")
