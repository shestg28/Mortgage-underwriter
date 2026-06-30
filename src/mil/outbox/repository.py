"""
Persistence gateway for the Transactional Outbox (ADR-007).

``OutboxRepository`` is the only way the platform writes and reads outbox rows.
Producing services call ``add()`` within their own transaction, so the outbox
row commits atomically with the state change that produced the event. The relay
calls ``fetch_pending()`` and ``mark_published()`` after commit.

This repository does not commit or roll back — the caller owns the unit of work
(the same contract as ``DocumentRepository`` and ``AuditWriter``).

Dependency rule: imports only from ``mil.outbox.models``, ``mil.kernel``, and
the Python standard library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from mil.outbox.models import OutboxEvent, OutboxStatus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from mil.kernel.events import DomainEvent


class OutboxRepository:
    """
    Read/write gateway for ``OutboxEvent`` rows.

    Construct with the caller's active session so that ``add()`` participates
    in the originating transaction (ADR-007 commit-before-publish).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, event: DomainEvent) -> OutboxEvent:
        """
        Append a domain event to the outbox within the current transaction.

        Returns the created ``OutboxEvent`` row (added to the session, not yet
        flushed). The row commits atomically with the caller's state change.
        """
        row = OutboxEvent.from_domain_event(event)
        self._session.add(row)
        return row

    def fetch_pending(self, *, limit: int = 100) -> list[OutboxEvent]:
        """
        Return up to ``limit`` unpublished outbox rows, oldest first.

        Used by the relay to find committed events awaiting publication.
        """
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .order_by(OutboxEvent.occurred_at.asc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def get_by_event_id(self, event_id: str) -> OutboxEvent | None:
        """Return the outbox row for a given originating event id, or ``None``."""
        stmt = select(OutboxEvent).where(OutboxEvent.event_id == event_id)
        return self._session.scalars(stmt).one_or_none()

    def mark_published(self, row: OutboxEvent) -> None:
        """Mark a row published (called by the relay after broker acceptance)."""
        row.mark_published()
        self._session.add(row)

    def pending_count(self) -> int:
        """Return the number of unpublished outbox rows."""
        stmt = select(OutboxEvent).where(OutboxEvent.status == OutboxStatus.PENDING)
        return len(list(self._session.scalars(stmt)))
