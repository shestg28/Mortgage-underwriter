"""
Persistence gateway for the Intelligence Orchestrator bounded context.

``WorkflowRepository`` persists and retrieves ``WorkflowRun`` aggregates (and
their owned ``WorkflowStep`` rows). It does not commit or roll back — the caller
owns the unit of work, so the run, its steps, and any outbox events written by
the orchestrator commit atomically together (ADR-007, ADR-008 per-job Unit of
Work).

The repository performs no business logic and emits no events itself. The
orchestrator service is responsible for outbox writes and job enqueue.

Dependency rule: imports only from ``mil.orchestrator.models``, ``mil.kernel``,
and the Python standard library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from mil.orchestrator.models import WorkflowRun

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class WorkflowRepository:
    """
    Read/write gateway for ``WorkflowRun`` aggregates.

    Construct with the caller's active session. ``save`` adds the run (with its
    cascaded steps) and flushes so server-side defaults and constraint
    violations surface within the caller's transaction.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, run: WorkflowRun) -> None:
        """
        Persist a workflow run and its owned steps.

        Adds the aggregate to the session and flushes. The owned ``steps`` are
        cascaded by the relationship. Commit is the caller's responsibility, so
        the run, its steps, and any outbox rows written in the same session
        commit atomically.
        """
        self._session.add(run)
        self._session.flush()

    def get_by_id(self, workflow_run_id: UUID) -> WorkflowRun | None:
        """Return the run with the given id, or ``None`` if not found."""
        return self._session.get(WorkflowRun, workflow_run_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> WorkflowRun | None:
        """
        Return the run with the given idempotency key, or ``None``.

        Used by the orchestrator to make ``start_workflow`` idempotent: a repeat
        trigger with the same key returns the existing run instead of creating
        a duplicate (ADR-008 replay behaviour).
        """
        stmt = select(WorkflowRun).where(WorkflowRun.idempotency_key == idempotency_key)
        return self._session.scalars(stmt).one_or_none()

    def get_for_application(self, application_id: UUID) -> list[WorkflowRun]:
        """Return all workflow runs for an application, most recent first."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.application_id == application_id)
            .order_by(WorkflowRun.created_at.desc())
        )
        return list(self._session.scalars(stmt))
