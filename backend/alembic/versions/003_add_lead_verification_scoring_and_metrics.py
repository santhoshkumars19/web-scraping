"""003_add_lead_verification_scoring_and_metrics

Revision ID: 003_add_lead_verification_scoring_and_metrics
Revises: 002_add_organization_merge_events
Create Date: 2026-09-12 13:00:00.000000+00:00

Adds lead_id, score, completeness_percentage, source_quality_score,
consistency_score, verification_reasons, and source_quality_details to lead_verifications.
Adds verified_count and confidence metrics to scraping_tasks.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_lead_verification_scoring_and_metrics"
down_revision: Union[str, None] = "002_add_organization_merge_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Alter lead_verifications table ─────────────────────────────────────
    op.add_column(
        "lead_verifications",
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_lead_verifications_lead_id_leads"),
        "lead_verifications",
        "leads",
        ["lead_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_verification_lead",
        "lead_verifications",
        ["lead_id"],
    )
    op.create_index(
        "ix_lead_verifications_lead",
        "lead_verifications",
        ["lead_id"],
        unique=False,
    )
    op.create_index(
        "ix_lead_verifications_org",
        "lead_verifications",
        ["organization_id"],
        unique=False,
    )

    op.add_column(
        "lead_verifications",
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "lead_verifications",
        sa.Column("completeness_percentage", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "lead_verifications",
        sa.Column("source_quality_score", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "lead_verifications",
        sa.Column("consistency_score", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "lead_verifications",
        sa.Column(
            "verification_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "lead_verifications",
        sa.Column(
            "source_quality_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    # Drop old organization uniqueness constraint so same organization can have verifications in distinct task leads
    try:
        op.drop_constraint("uq_verification_org", "lead_verifications", type_="unique")
    except Exception:
        pass

    # ── 2. Alter scraping_tasks table ─────────────────────────────────────────
    op.add_column(
        "scraping_tasks",
        sa.Column("verified_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scraping_tasks",
        sa.Column("high_confidence_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scraping_tasks",
        sa.Column("medium_confidence_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scraping_tasks",
        sa.Column("low_confidence_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    # Scraping tasks metrics
    op.drop_column("scraping_tasks", "low_confidence_count")
    op.drop_column("scraping_tasks", "medium_confidence_count")
    op.drop_column("scraping_tasks", "high_confidence_count")
    op.drop_column("scraping_tasks", "verified_count")

    # Lead verifications columns
    op.drop_column("lead_verifications", "source_quality_details")
    op.drop_column("lead_verifications", "verification_reasons")
    op.drop_column("lead_verifications", "consistency_score")
    op.drop_column("lead_verifications", "source_quality_score")
    op.drop_column("lead_verifications", "completeness_percentage")
    op.drop_column("lead_verifications", "score")
    op.drop_index("ix_lead_verifications_org", table_name="lead_verifications")
    op.drop_index("ix_lead_verifications_lead", table_name="lead_verifications")
    op.drop_constraint("uq_verification_lead", "lead_verifications", type_="unique")
    op.drop_constraint(op.f("fk_lead_verifications_lead_id_leads"), "lead_verifications", type_="foreignkey")
    op.drop_column("lead_verifications", "lead_id")
    op.create_unique_constraint("uq_verification_org", "lead_verifications", ["organization_id"])
