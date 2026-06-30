"""Add core.documents table — Sprint 3C Document bounded context.

Creates the ``core.documents`` table that stores immutable document asset
records. Each row represents a source file uploaded to a mortgage application.
The ``content_hash`` and ``storage_reference`` columns are set once at ingestion
and are never updated — they are the platform's tamper-evidence mechanism.

Tables created:
    core.documents    — immutable document asset registry

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # core.documents
    #
    # FK dependencies:
    #   application_id → core.applications.id  (required)
    #   party_id       → core.parties.id        (optional)
    #
    # content_hash and storage_reference are set once at ingestion.
    # ingestion_status tracks the intelligence pipeline state (US2).
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("party_id", sa.UUID(), nullable=True),
        sa.Column("uploaded_by", sa.UUID(), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        # SHA-256 hex digest (64 chars). Immutable after ingestion.
        sa.Column("content_hash", sa.String(128), nullable=False),
        # Content-addressed storage reference. Immutable after ingestion.
        sa.Column("storage_reference", sa.Text(), nullable=False),
        sa.Column(
            "ingestion_status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["core.applications.id"],
            name=op.f("fk_documents_application_id_applications"),
        ),
        sa.ForeignKeyConstraint(
            ["party_id"],
            ["core.parties.id"],
            name=op.f("fk_documents_party_id_parties"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        schema="core",
    )

    # tenant_id: primary filter for all document queries
    op.create_index(
        op.f("ix_core_documents_tenant_id"),
        "documents",
        ["tenant_id"],
        unique=False,
        schema="core",
    )

    # application_id: primary join path from application to its documents
    op.create_index(
        op.f("ix_core_documents_application_id"),
        "documents",
        ["application_id"],
        unique=False,
        schema="core",
    )

    # content_hash: duplicate-detection and tamper-evidence lookups
    op.create_index(
        op.f("ix_core_documents_content_hash"),
        "documents",
        ["content_hash"],
        unique=False,
        schema="core",
    )

    # ingestion_status: pipeline monitoring queries (e.g. "show all PENDING")
    op.create_index(
        op.f("ix_core_documents_ingestion_status"),
        "documents",
        ["ingestion_status"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("documents", schema="core")
