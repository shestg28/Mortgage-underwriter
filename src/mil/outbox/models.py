"""
ORM model for the Transactional Outbox (ADR-007).

The outbox is a platform-level mechanism that makes cross-context domain-event
publication safe under a multi-process, broker-backed topology. A producing
service writes the event as an ``OutboxEvent`` row **in the same database
transaction** as the state change that produced it. Because the business row
and the outbox row commit (or roll back) together, the event is durably
recorded if and only if the state change is — eliminating the dual-write
problem (ADR-007).

A separate relay (``mil.outbox.relay``) publishes committed, unpublished rows
to the broker after commit and marks them published. This sprint persists
only — no broker publishing is implemented.

The outbox is analogous to the audit log: a shared, append-only platform store
written in-transaction and imported directly by producing contexts (the same
way ``mil.audit`` is). It is NOT a bounded context with business logic.

**Audit is not routed through the outbox.** Audit events remain synchronous and
in-transaction (ADR-007, explicit decision). Only cross-context ``DomainEvent``s
flow through the outbox.

Schema: ``orchestrator`` PostgreSQL schema (the orchestrator is the sole
producer in US2 Sprint 1; ADR-007 treats the outbox as a platform mechanism
whose physical home may be revisited when other producers adopt it).

Dependency rule: imports only from ``mil.kernel`` and the Python standard
library. No bounded context is imported.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mil.kernel.db import Base

if TYPE_CHECKING:
    from mil.kernel.events import DomainEvent


class OutboxStatus(enum.StrEnum):
    """
    Delivery state of an outbox row.

    PENDING   — committed to the outbox, not yet published by the relay.
    PUBLISHED — accepted by the broker; the relay has marked it delivered.
    """

    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"


class OutboxEvent(Base):
    """
    A cross-context domain event awaiting (or having completed) publication.

    Written in the same transaction as the originating state change (ADR-007).
    The ``event_id`` carries the originating ``DomainEvent.event_id`` and is
    unique, so the same logical event cannot be enqueued twice even under
    at-least-once upstream retries (ADR-008 duplicate prevention).

    ``payload`` is the JSON-safe serialisation produced by
    ``DomainEvent.to_dict()`` — enough for any subscriber to act without a
    follow-up query.
    """

    __tablename__ = "outbox_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_outbox_events_event_id"),
        {"schema": "orchestrator"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # The originating DomainEvent.event_id — stable, unique, dedup anchor.
    event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    # Threads the whole pipeline execution together (ADR-009).
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=OutboxStatus.PENDING)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @classmethod
    def from_domain_event(cls, event: DomainEvent) -> OutboxEvent:
        """
        Build a PENDING outbox row from a typed ``DomainEvent``.

        Captures the event's id, type, tenant, correlation id, occurrence time,
        and full serialised payload. The row is returned unattached to a
        session — the producing repository adds it within the originating
        transaction.
        """
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            event_id=event.event_id,
            event_type=type(event).__name__,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            payload=event.to_dict(),
            status=OutboxStatus.PENDING,
            occurred_at=event.occurred_at,
            created_at=now,
        )

    def mark_published(self) -> None:
        """Mark this event as published by the relay."""
        self.status = OutboxStatus.PUBLISHED
        self.published_at = datetime.now(UTC)

    @property
    def status_enum(self) -> OutboxStatus:
        """Return the current status as a typed enum value."""
        return OutboxStatus(self.status)

    @property
    def is_published(self) -> bool:
        return self.status == OutboxStatus.PUBLISHED

    def __repr__(self) -> str:
        return (
            f"<OutboxEvent id={self.id} type={self.event_type} "
            f"status={self.status} corr={self.correlation_id}>"
        )
