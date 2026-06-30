"""
ORM model for the Audit & Governance bounded context.

``AuditEvent`` represents a single append-only entry in the platform audit log.
Every significant action performed by the platform or by its users is recorded
here (Engineering Constitution, Principle VIII — Auditability).

Design constraints:
- No UPDATE or DELETE is permitted at the database level on ``audit.audit_events``.
- ``sequence_number`` is a monotonic server-generated BigInteger. A gap in
  sequence numbers indicates a potential tamper event and must be investigated.
- ``event_data`` stores event-specific payload as JSON. Its schema varies by
  ``event_type`` but must always be serialisable to a plain dict.
- ``actor_id`` is NULL for system-driven events (background jobs, automated
  pipeline steps); non-NULL for user-initiated actions.

Schema: ``audit`` PostgreSQL schema.

Dependency rule: imports only from ``mil.kernel.db`` and the Python standard
library. No bounded context may import from another bounded context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from mil.kernel.db import Base


class AuditEvent(Base):
    """
    An immutable record of a significant platform or user action.

    ``entity_type`` identifies the domain entity affected (e.g. "APPLICATION",
    "PARTY", "FINDING"). ``entity_id`` is that entity's UUID.

    ``application_id`` correlates events across a mortgage application's full
    lifecycle, enabling reconstruction of the complete audit trail for any
    given application without joining to other tables.

    ``actor_type`` is either "USER" (an authenticated human or service account)
    or "SYSTEM" (an automated pipeline step). Human actor events carry a
    non-null ``actor_id``.

    ``sequence_number`` is assigned by the database via a dedicated sequence.
    The ORM never sets this field; it is populated by the database on INSERT
    and read back after flush. Its monotonic guarantee enables gap detection.
    """

    __tablename__ = "audit_events"
    __table_args__ = {"schema": "audit"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    application_id: Mapped[UUID | None] = mapped_column(nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(nullable=True)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False, default="SYSTEM")
    event_data: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    # Server-side BigInteger sequence — never set by the ORM; populated by the
    # database on INSERT. Reading it after flush requires a DB round-trip.
    sequence_number: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=False,
        server_default="nextval('audit.audit_events_sequence_number_seq')",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent seq={self.sequence_number} "
            f"type={self.event_type} entity={self.entity_type}/{self.entity_id}>"
        )
