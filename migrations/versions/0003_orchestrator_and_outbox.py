"""Add orchestrator schema — workflow runs, steps, and the transactional outbox.

US2 Sprint 1 — Intelligence Orchestrator Foundation. Creates the coordination
tables for the Intelligence Orchestrator and the Transactional Outbox (ADR-007).

Tables created:
    orchestrator.workflow_runs   — one execution of an intelligence pipeline;
                                   pins the version set (ADR-009) and carries the
                                   correlation id; idempotency_key is unique.
    orchestrator.workflow_steps  — ordered coordination records within a run;
                                   (workflow_run_id, step_name) is unique.
    orchestrator.outbox_events   — committed cross-context domain events awaiting
                                   relay publication (ADR-007); event_id is unique.

Audit events are NOT routed through the outbox — audit remains synchronous and
in-transaction (ADR-007, explicit decision).

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS orchestrator")

    # ------------------------------------------------------------------
    # orchestrator.workflow_runs
    #
    # FK: application_id → core.applications.id
    # Pinned version set (ADR-009) and correlation id (ADR-009) are fixed at
    # run creation. idempotency_key is unique (ADR-008 duplicate prevention).
    # ------------------------------------------------------------------
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("workflow_type", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("pinned_policy_version", sa.String(100), nullable=False),
        sa.Column("pinned_extraction_version", sa.String(100), nullable=False),
        sa.Column("pinned_inference_version", sa.String(100), nullable=False),
        sa.Column("pinned_prompt_version", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["core.applications.id"],
            name=op.f("fk_workflow_runs_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_runs")),
        sa.UniqueConstraint("idempotency_key", name="uq_workflow_runs_idempotency_key"),
        schema="orchestrator",
    )
    op.create_index(
        op.f("ix_orchestrator_workflow_runs_tenant_id"),
        "workflow_runs",
        ["tenant_id"],
        unique=False,
        schema="orchestrator",
    )
    op.create_index(
        op.f("ix_orchestrator_workflow_runs_application_id"),
        "workflow_runs",
        ["application_id"],
        unique=False,
        schema="orchestrator",
    )
    op.create_index(
        op.f("ix_orchestrator_workflow_runs_correlation_id"),
        "workflow_runs",
        ["correlation_id"],
        unique=False,
        schema="orchestrator",
    )

    # ------------------------------------------------------------------
    # orchestrator.workflow_steps
    #
    # FK: workflow_run_id → orchestrator.workflow_runs.id
    # (workflow_run_id, step_name) is unique (ADR-008 duplicate prevention).
    # ------------------------------------------------------------------
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_run_id", sa.UUID(), nullable=False),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["workflow_run_id"],
            ["orchestrator.workflow_runs.id"],
            name=op.f("fk_workflow_steps_workflow_run_id_workflow_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_steps")),
        sa.UniqueConstraint("workflow_run_id", "step_name", name="uq_workflow_steps_run_step"),
        schema="orchestrator",
    )
    op.create_index(
        op.f("ix_orchestrator_workflow_steps_workflow_run_id"),
        "workflow_steps",
        ["workflow_run_id"],
        unique=False,
        schema="orchestrator",
    )

    # ------------------------------------------------------------------
    # orchestrator.outbox_events
    #
    # Cross-context domain events written in the same transaction as the
    # originating state change (ADR-007). event_id is unique so the same
    # logical event cannot be enqueued twice (ADR-008).
    # ------------------------------------------------------------------
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False, server_default=sa.text("''")),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox_events")),
        sa.UniqueConstraint("event_id", name="uq_outbox_events_event_id"),
        schema="orchestrator",
    )
    # status: the relay polls for PENDING rows to publish.
    op.create_index(
        op.f("ix_orchestrator_outbox_events_status"),
        "outbox_events",
        ["status"],
        unique=False,
        schema="orchestrator",
    )
    op.create_index(
        op.f("ix_orchestrator_outbox_events_correlation_id"),
        "outbox_events",
        ["correlation_id"],
        unique=False,
        schema="orchestrator",
    )


def downgrade() -> None:
    op.drop_table("outbox_events", schema="orchestrator")
    op.drop_table("workflow_steps", schema="orchestrator")
    op.drop_table("workflow_runs", schema="orchestrator")
    op.execute("DROP SCHEMA IF EXISTS orchestrator")
