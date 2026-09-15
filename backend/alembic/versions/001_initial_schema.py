"""001_initial_schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-09-12 11:00:00.000000+00:00

Initial LeadScout core database schema:
- users
- scraping_tasks
- organizations
- task_organizations
- leads
- lead_verifications
- websites
- contacts
- phone_numbers
- email_addresses
- source_pages
- social_links
- extracted_fields
- scraping_logs
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Sequence for human-readable Task ID ───────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS task_id_seq START WITH 1 INCREMENT BY 1;")

    # ── 1. Users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("USER", "ADMIN", name="user_role_enum"),
            server_default="USER",
            nullable=False,
        ),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── 2. Scraping Tasks ─────────────────────────────────────────────────────
    op.create_table(
        "scraping_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=False),
        sa.Column("keyword", sa.String(length=500), nullable=False),
        sa.Column("search_radius", sa.Integer(), server_default="25", nullable=False),
        sa.Column("max_results", sa.Integer(), server_default="100", nullable=False),
        sa.Column("max_pages_per_site", sa.Integer(), server_default="5", nullable=False),
        sa.Column("crawl_depth", sa.Integer(), server_default="2", nullable=False),
        sa.Column("selected_fields", sa.JSON(), nullable=True),
        sa.Column("follow_internal_links", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("prioritize_contact", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("prioritize_about", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("prioritize_admissions", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("prioritize_staff_management", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", name="task_status_enum"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "current_stage",
            sa.Enum(
                "CREATING_TASK", "DISCOVERING", "FINDING_WEBSITES", "CRAWLING",
                "EXTRACTING", "CLEANING", "DEDUPLICATING", "VERIFYING", "SAVING", "COMPLETED",
                name="task_stage_enum",
            ),
            server_default="CREATING_TASK",
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("results_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("websites_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("websites_crawled", sa.Integer(), server_default="0", nullable=False),
        sa.Column("phones_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("emails_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("addresses_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicates_removed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_websites", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_task_progress_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_scraping_tasks_task_id", "scraping_tasks", ["task_id"], unique=True)
    op.create_index("ix_scraping_tasks_user_id", "scraping_tasks", ["user_id"])
    op.create_index("ix_scraping_tasks_status", "scraping_tasks", ["status"])

    # ── 3. Organizations ──────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=255), nullable=True),
        sa.Column("pincode", sa.String(length=20), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"])
    op.create_index("ix_organizations_category", "organizations", ["category"])
    op.create_index("ix_organizations_city_state", "organizations", ["city", "state"])
    op.create_index("ix_organizations_pincode", "organizations", ["pincode"])

    # ── 4. Task Organizations (M2M) ───────────────────────────────────────────
    op.create_table(
        "task_organizations",
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["scraping_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "organization_id"),
    )

    # ── 5. Leads ──────────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ARCHIVED", "DELETED", name="lead_status_enum"),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "verification_status",
            sa.Enum("PENDING", "LOW", "MEDIUM", "HIGH", name="lead_verification_status_enum"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["scraping_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "organization_id", name="uq_lead_task_org"),
    )
    op.create_index("ix_leads_task_id", "leads", ["task_id"])
    op.create_index("ix_leads_organization_id", "leads", ["organization_id"])

    # ── 6. Lead Verifications ─────────────────────────────────────────────────
    op.create_table(
        "lead_verifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "LOW", "MEDIUM", "HIGH", name="verification_status_enum"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("fields_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_fields", sa.Integer(), server_default="0", nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_verification_org"),
    )
    op.create_index("ix_lead_verifications_organization_id", "lead_verifications", ["organization_id"])

    # ── 7. Websites ───────────────────────────────────────────────────────────
    op.create_table(
        "websites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("normalized_url", sa.String(length=2048), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("is_official", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "CRAWLING", "CRAWLED", "FAILED", "BLOCKED", name="website_status_enum"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "normalized_url", name="uq_website_org_url"),
    )
    op.create_index("ix_websites_organization_id", "websites", ["organization_id"])
    op.create_index("ix_websites_normalized_url", "websites", ["normalized_url"])
    op.create_index("ix_websites_domain", "websites", ["domain"])

    # ── 8. Contacts ───────────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("designation", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])

    # ── 9. Phone Numbers ──────────────────────────────────────────────────────
    op.create_table(
        "phone_numbers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=True),
        sa.Column("phone_number", sa.String(length=50), nullable=False),
        sa.Column("normalized_phone", sa.String(length=20), nullable=False),
        sa.Column(
            "phone_type",
            sa.Enum("MAIN", "ALTERNATE", "OFFICE", "ADMISSIONS", "LANDLINE", "WHATSAPP", "OTHER", name="phone_type_enum"),
            server_default="MAIN",
            nullable=False,
        ),
        sa.Column("is_whatsapp", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "normalized_phone", name="uq_phone_org_normalized"),
    )
    op.create_index("ix_phone_numbers_organization_id", "phone_numbers", ["organization_id"])
    op.create_index("ix_phone_numbers_contact_id", "phone_numbers", ["contact_id"])
    op.create_index("ix_phone_numbers_normalized_phone", "phone_numbers", ["normalized_phone"])

    # ── 10. Email Addresses ───────────────────────────────────────────────────
    op.create_table(
        "email_addresses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("normalized_email", sa.String(length=320), nullable=False),
        sa.Column(
            "email_type",
            sa.Enum("GENERAL", "CONTACT", "ADMISSIONS", "MANAGEMENT", "OTHER", name="email_type_enum"),
            server_default="GENERAL",
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "normalized_email", name="uq_email_org_normalized"),
    )
    op.create_index("ix_email_addresses_organization_id", "email_addresses", ["organization_id"])
    op.create_index("ix_email_addresses_contact_id", "email_addresses", ["contact_id"])
    op.create_index("ix_email_addresses_normalized_email", "email_addresses", ["normalized_email"])

    # ── 11. Source Pages ──────────────────────────────────────────────────────
    op.create_table(
        "source_pages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("website_id", sa.UUID(), nullable=True),
        sa.Column("task_id", sa.UUID(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("page_title", sa.String(length=1024), nullable=True),
        sa.Column(
            "page_type",
            sa.Enum(
                "HOME", "ABOUT", "CONTACT", "ADMISSIONS", "MANAGEMENT",
                "PRINCIPAL", "FACULTY", "STAFF", "BRANCH", "LOCATION",
                "INFRASTRUCTURE", "OTHER",
                name="page_type_enum",
            ),
            server_default="OTHER",
            nullable=False,
        ),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["scraping_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("website_id", "normalized_url", name="uq_source_page_website_url"),
    )
    op.create_index("ix_source_pages_organization_id", "source_pages", ["organization_id"])
    op.create_index("ix_source_pages_website_id", "source_pages", ["website_id"])
    op.create_index("ix_source_pages_task_id", "source_pages", ["task_id"])
    op.create_index("ix_source_pages_normalized_url", "source_pages", ["normalized_url"])
    op.create_index("ix_source_pages_page_type", "source_pages", ["page_type"])

    # ── 12. Social Links ──────────────────────────────────────────────────────
    op.create_table(
        "social_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("FACEBOOK", "INSTAGRAM", "LINKEDIN", "TWITTER", "YOUTUBE", "OTHER", name="social_platform_enum"),
            server_default="OTHER",
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("is_official", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "normalized_url", name="uq_social_link_org_normalized"),
    )
    op.create_index("ix_social_links_organization_id", "social_links", ["organization_id"])
    op.create_index("ix_social_links_org_platform", "social_links", ["organization_id", "platform"])
    op.create_index("ix_social_links_normalized_url", "social_links", ["normalized_url"])

    # ── 13. Extracted Fields ──────────────────────────────────────────────────
    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("source_page_id", sa.UUID(), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_page_id"], ["source_pages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_extracted_fields_organization_id", "extracted_fields", ["organization_id"])
    op.create_index("ix_extracted_fields_source_page_id", "extracted_fields", ["source_page_id"])
    op.create_index("ix_extracted_fields_field_name", "extracted_fields", ["field_name"])
    op.create_index("ix_extracted_fields_org_field", "extracted_fields", ["organization_id", "field_name"])
    op.create_index("ix_extracted_fields_page_field", "extracted_fields", ["source_page_id", "field_name"])
    op.create_index("ix_extracted_fields_normalized", "extracted_fields", ["normalized_value"])

    # ── 14. Scraping Logs ─────────────────────────────────────────────────────
    op.create_table(
        "scraping_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("website_id", sa.UUID(), nullable=True),
        sa.Column(
            "level",
            sa.Enum("INFO", "WARNING", "ERROR", name="log_level_enum"),
            server_default="INFO",
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["scraping_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scraping_logs_task_id", "scraping_logs", ["task_id"])
    op.create_index("ix_scraping_logs_organization_id", "scraping_logs", ["organization_id"])
    op.create_index("ix_scraping_logs_website_id", "scraping_logs", ["website_id"])
    op.create_index("ix_scraping_logs_task_created", "scraping_logs", ["task_id", "created_at"])
    op.create_index("ix_scraping_logs_level", "scraping_logs", ["level"])
    op.create_index("ix_scraping_logs_event_type", "scraping_logs", ["event_type"])


def downgrade() -> None:
    # Drop tables in reverse topological order
    op.drop_table("scraping_logs")
    op.drop_table("extracted_fields")
    op.drop_table("social_links")
    op.drop_table("source_pages")
    op.drop_table("email_addresses")
    op.drop_table("phone_numbers")
    op.drop_table("contacts")
    op.drop_table("websites")
    op.drop_table("lead_verifications")
    op.drop_table("leads")
    op.drop_table("task_organizations")
    op.drop_table("organizations")
    op.drop_table("scraping_tasks")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "log_level_enum",
        "social_platform_enum",
        "page_type_enum",
        "email_type_enum",
        "phone_type_enum",
        "website_status_enum",
        "verification_status_enum",
        "lead_verification_status_enum",
        "lead_status_enum",
        "task_stage_enum",
        "task_status_enum",
        "user_role_enum",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS task_id_seq;")
