"""002_add_organization_merge_events

Revision ID: 002_add_organization_merge_events
Revises: 001_initial_schema
Create Date: 2026-09-12 12:00:00.000000+00:00

Adds organization_merge_events audit table for organization deduplication tracking.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_organization_merge_events"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization_merge_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "source_organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "target_organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "match_score",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "match_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["target_organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_merge_events_target_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_merge_events")),
    )

    op.create_index(
        "ix_org_merge_source",
        "organization_merge_events",
        ["source_organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_merge_target",
        "organization_merge_events",
        ["target_organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_org_merge_target", table_name="organization_merge_events")
    op.drop_index("ix_org_merge_source", table_name="organization_merge_events")
    op.drop_table("organization_merge_events")
