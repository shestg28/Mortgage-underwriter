"""Add core.document_ocr_results — persisted, immutable OCR output (US2 Sprint 2).

Stores the text and layout an OCR engine produced for a document, separately
from the custody record (core.documents). Rows are immutable and never updated.

Determinism (Principle XII): (document_id, provider_version) is unique — the
same document under the same provider version yields one stored result.

Tables created:
    core.document_ocr_results — immutable OCR output per (document, provider version)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # core.document_ocr_results
    #
    # FK dependencies:
    #   document_id     → core.documents.id              (source document)
    #   workflow_run_id → orchestrator.workflow_runs.id  (producing run / lineage)
    #
    # Immutable: created once by the OCR worker, never updated.
    # ------------------------------------------------------------------
    op.create_table(
        "document_ocr_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("workflow_run_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("provider_version", sa.String(100), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("pages", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["core.documents.id"],
            name=op.f("fk_document_ocr_results_document_id_documents"),
        ),
        sa.ForeignKeyConstraint(
            ["workflow_run_id"],
            ["orchestrator.workflow_runs.id"],
            name=op.f("fk_document_ocr_results_workflow_run_id_workflow_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_ocr_results")),
        sa.UniqueConstraint(
            "document_id", "provider_version", name="uq_document_ocr_results_document_version"
        ),
        schema="core",
    )

    # Primary lookup path: all OCR results for a document.
    op.create_index(
        op.f("ix_core_document_ocr_results_document_id"),
        "document_ocr_results",
        ["document_id"],
        unique=False,
        schema="core",
    )
    # Lineage queries: all OCR output produced by a workflow run.
    op.create_index(
        op.f("ix_core_document_ocr_results_workflow_run_id"),
        "document_ocr_results",
        ["workflow_run_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_core_document_ocr_results_tenant_id"),
        "document_ocr_results",
        ["tenant_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("document_ocr_results", schema="core")
