"""Create core and audit schemas — Sprint 3B baseline.

This migration establishes the foundational tables for the Platform Foundation
(User Story 1). It covers all tables in the ``core`` PostgreSQL schema plus the
``audit.audit_events`` append-only event log.

Tables created:
    core.users                — authenticated platform users
    core.roles                — RBAC roles
    core.role_assignments     — user-to-role bindings (soft-revocation)
    core.policy_packs         — versioned policy pack registry
    core.applications         — mortgage application aggregate roots
    core.parties              — parties within a mortgage application
    audit.audit_events        — append-only platform audit log

Revision ID: 0001
Revises:
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Schemas
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    # ------------------------------------------------------------------
    # core.users
    # (No FK dependencies — created first)
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("external_identity_id", sa.String(255), nullable=False),
        sa.Column("email_hash", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        schema="core",
    )
    op.create_index(
        op.f("ix_core_users_tenant_id"),
        "users",
        ["tenant_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_core_users_external_identity_id"),
        "users",
        ["external_identity_id"],
        unique=False,
        schema="core",
    )

    # ------------------------------------------------------------------
    # core.policy_packs
    # (FK: created_by → core.users.id — created after users)
    # ------------------------------------------------------------------
    op.create_table(
        "policy_packs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["core.users.id"],
            name=op.f("fk_policy_packs_created_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy_packs")),
        schema="core",
    )
    op.create_index(
        op.f("ix_core_policy_packs_tenant_id"),
        "policy_packs",
        ["tenant_id"],
        unique=False,
        schema="core",
    )

    # ------------------------------------------------------------------
    # core.roles
    # (No FK dependencies)
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        schema="core",
    )
    op.create_index(
        op.f("ix_core_roles_tenant_id"),
        "roles",
        ["tenant_id"],
        unique=False,
        schema="core",
    )

    # ------------------------------------------------------------------
    # core.role_assignments
    # (FK: user_id, assigned_by → core.users.id; role_id → core.roles.id)
    # ------------------------------------------------------------------
    op.create_table(
        "role_assignments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("assigned_by", sa.UUID(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["core.users.id"],
            name=op.f("fk_role_assignments_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["core.roles.id"],
            name=op.f("fk_role_assignments_role_id_roles"),
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["core.users.id"],
            name=op.f("fk_role_assignments_assigned_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_assignments")),
        schema="core",
    )
    op.create_index(
        op.f("ix_core_role_assignments_user_id"),
        "role_assignments",
        ["user_id"],
        unique=False,
        schema="core",
    )

    # ------------------------------------------------------------------
    # core.applications
    # (FK: created_by → core.users.id; active_policy_pack_id → core.policy_packs.id)
    # ------------------------------------------------------------------
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("los_reference", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("active_policy_pack_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["core.users.id"],
            name=op.f("fk_applications_created_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["active_policy_pack_id"],
            ["core.policy_packs.id"],
            name=op.f("fk_applications_active_policy_pack_id_policy_packs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        schema="core",
    )
    op.create_index(
        op.f("ix_core_applications_tenant_id"),
        "applications",
        ["tenant_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_core_applications_status"),
        "applications",
        ["status"],
        unique=False,
        schema="core",
    )

    # ------------------------------------------------------------------
    # core.parties
    # (FK: application_id → core.applications.id)
    # ------------------------------------------------------------------
    op.create_table(
        "parties",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("party_type", sa.String(50), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["core.applications.id"],
            name=op.f("fk_parties_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_parties")),
        schema="core",
    )
    op.create_index(
        op.f("ix_core_parties_application_id"),
        "parties",
        ["application_id"],
        unique=False,
        schema="core",
    )

    # ------------------------------------------------------------------
    # audit.audit_events
    # Append-only. No FK constraints (entity_id varies by entity_type).
    # sequence_number is BIGINT with a dedicated sequence for monotonic ordering.
    # ------------------------------------------------------------------
    op.execute("CREATE SEQUENCE IF NOT EXISTS audit.audit_events_sequence_number_seq")
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column(
            "actor_type",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'SYSTEM'"),
        ),
        sa.Column(
            "event_data",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "sequence_number",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text(
                "nextval('audit.audit_events_sequence_number_seq')"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
        sa.UniqueConstraint(
            "sequence_number", name=op.f("uq_audit_events_sequence_number")
        ),
        schema="audit",
    )
    op.create_index(
        op.f("ix_audit_audit_events_tenant_id"),
        "audit_events",
        ["tenant_id"],
        unique=False,
        schema="audit",
    )
    op.create_index(
        op.f("ix_audit_audit_events_application_id"),
        "audit_events",
        ["application_id"],
        unique=False,
        schema="audit",
    )
    op.create_index(
        op.f("ix_audit_audit_events_entity_id"),
        "audit_events",
        ["entity_type", "entity_id"],
        unique=False,
        schema="audit",
    )


def downgrade() -> None:
    op.drop_table("audit_events", schema="audit")
    op.execute("DROP SEQUENCE IF EXISTS audit.audit_events_sequence_number_seq")
    op.drop_table("parties", schema="core")
    op.drop_table("applications", schema="core")
    op.drop_table("role_assignments", schema="core")
    op.drop_table("roles", schema="core")
    op.drop_table("policy_packs", schema="core")
    op.drop_table("users", schema="core")
    op.execute("DROP SCHEMA IF EXISTS audit")
    op.execute("DROP SCHEMA IF EXISTS core")
