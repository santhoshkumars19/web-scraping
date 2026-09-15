"""005_add_auth_and_email_normalized

Revision ID: 005_add_auth_and_email_normalized
Revises: 004_add_celery_task_id
Create Date: 2026-09-13 10:00:00.000000+00:00

Adds email_normalized column and unique index to users table with backfill.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_add_auth_and_email_normalized"
down_revision: Union[str, None] = "004_add_celery_task_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable initially so existing rows don't violate not-null
    op.add_column(
        "users",
        sa.Column("email_normalized", sa.String(length=320), nullable=True),
    )

    # 2. Backfill existing rows safely with lower(trim(email))
    op.execute(
        "UPDATE users SET email_normalized = LOWER(TRIM(email)) WHERE email_normalized IS NULL;"
    )

    # 3. Alter column to NOT NULL
    op.alter_column(
        "users",
        "email_normalized",
        existing_type=sa.String(length=320),
        nullable=False,
    )

    # 4. Create unique index
    op.create_index(
        op.f("ix_users_email_normalized"),
        "users",
        ["email_normalized"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_users_email_normalized"),
        table_name="users",
    )
    op.drop_column("users", "email_normalized")
