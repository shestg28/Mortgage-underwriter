"""
Worker process startup infrastructure.

This module provides the scaffolding a background worker needs to run:

- build the dependency-injection container,
- create a database session factory,
- resolve shared dependencies (the ``JobQueue``),
- execute a job within a per-job Unit of Work.

It deliberately contains **no worker business logic**. The actual work of a
step (OCR, extraction, evidence, findings) is supplied by an injected
``JobHandler`` in a later sprint. ``process_next`` is the execution harness that
runs that handler safely; it is infrastructure, not domain logic.

Per-job Unit of Work (ADR-008): each job runs in a single database transaction.
On success the transaction commits and the job is acknowledged; on failure it
rolls back and the job is rejected (requeued within its retry budget). Because a
crash between side-effect and acknowledgement causes redelivery, handlers must
be idempotent — which the deterministic keys and unique constraints of ADR-008
guarantee.

Correlation propagation (ADR-009): the job's ``correlation_id`` is bound to the
request context before the handler runs, so the worker's logs, audit writes, and
any emitted events all carry the same end-to-end trace id. No pipeline object
loses the correlation id.

Dependency rule: imports only from ``mil.kernel``, the persistence layer, and
the Python standard library. No bounded context business logic is imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mil.kernel.config import get_settings
from mil.kernel.container import build_container
from mil.kernel.context import RequestContext, reset_request_context, set_request_context
from mil.kernel.job_queue import JobQueue

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from mil.kernel.config import Settings
    from mil.kernel.container import Container
    from mil.kernel.job_queue import Job


class JobHandler(Protocol):
    """
    Callable that executes one job within an open database session.

    The handler is the worker's business logic — supplied by the bounded
    context that owns the step (US2 Sprint 2+). The bootstrap never implements
    one; it only invokes the injected handler inside a Unit of Work.
    """

    def __call__(self, session: Session, job: Job) -> None:
        """Execute the job. Must not commit — the harness owns the transaction."""
        ...


@dataclass
class WorkerContext:
    """
    Resolved runtime dependencies for a worker process.

    Attributes:
        container:        The application DI container.
        session_factory:  Factory producing a fresh ``Session`` per job.
        job_queue:        The platform job queue (resolved from the container).
    """

    container: Container
    session_factory: sessionmaker[Session]
    job_queue: JobQueue


def build_worker_context(
    *,
    settings: Settings | None = None,
    container: Container | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> WorkerContext:
    """
    Assemble a ``WorkerContext`` for a worker process.

    Mirrors the API process bootstrap in ``main.py``: build the container from
    settings, create a synchronous session factory, and resolve the job queue.

    All collaborators are injectable so tests can supply fakes without touching
    real infrastructure. When not supplied:

    - ``settings`` defaults to ``get_settings()``,
    - ``container`` defaults to ``build_container(settings)``,
    - ``session_factory`` defaults to a factory bound to a new engine built from
      ``settings.database_sync_url`` (the engine connects lazily, not at build
      time).

    Returns:
        A fully resolved ``WorkerContext``.
    """
    resolved_settings = settings if settings is not None else get_settings()
    resolved_container = container if container is not None else build_container(resolved_settings)

    if session_factory is not None:
        factory = session_factory
    else:
        engine = create_engine(resolved_settings.database_sync_url)
        factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    job_queue = resolved_container.resolve(JobQueue)
    return WorkerContext(
        container=resolved_container,
        session_factory=factory,
        job_queue=job_queue,
    )


def process_next(ctx: WorkerContext, handler: JobHandler) -> bool:
    """
    Claim and process the next available job, if any, in a Unit of Work.

    Steps:
      1. Dequeue a job; return ``False`` immediately if the queue is empty.
      2. Bind the job's correlation id to the request context (ADR-009).
      3. Open a session and invoke ``handler`` within it.
      4. On success: commit and acknowledge the job.
         On failure: roll back, reject (requeue within the retry budget), and
         re-raise so the caller is aware.

    Returns:
        ``True`` if a job was claimed and processed (the harness handled it),
        ``False`` if the queue was empty.

    The handler must not commit; the transaction boundary belongs to this
    harness so that the business write, any workflow/step state, and any outbox
    rows commit together (ADR-007 / ADR-008).
    """
    job = ctx.job_queue.dequeue()
    if job is None:
        return False

    correlation_id = str(job.payload.get("correlation_id", "")) if job.payload else ""
    context = RequestContext(correlation_id=correlation_id) if correlation_id else RequestContext()
    token = set_request_context(context)

    session = ctx.session_factory()
    try:
        handler(session, job)
        session.commit()
        ctx.job_queue.acknowledge(job.job_id)
    except Exception:
        session.rollback()
        ctx.job_queue.reject(job.job_id, requeue=True)
        raise
    finally:
        session.close()
        reset_request_context(token)

    return True
