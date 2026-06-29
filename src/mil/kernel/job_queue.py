"""
JobQueue abstraction for the MIL Platform.

The ``JobQueue`` interface is the platform-level primitive for dispatching and
processing asynchronous work units.  The Intelligence Orchestrator enqueues
jobs; background worker processes dequeue and execute them.

The concrete backing implementation (in-process, Redis, AMQP, etc.) is
registered in the dependency injection container at startup.  All platform
code resolves ``JobQueue`` from the container — no direct dependency on a
concrete broker exists in the domain layer.

This module provides:

- ``Job`` — an immutable frozen descriptor with idempotency guarantees.
- ``JobQueue`` — abstract interface for enqueue/dequeue/acknowledge cycles.
- ``InProcessJobQueue`` — synchronous, in-memory implementation for
  development and testing.

Idempotency: ``InProcessJobQueue`` deduplicates enqueue calls by
``idempotency_key``.  A job with the same key is silently skipped if an
identical key is already pending or processing.  Upon acknowledgement the
key is released so the same logical job can be re-enqueued in future
(e.g. after a periodic delay or a new trigger).

Dependency rule: this module imports only from the Python standard library.
No bounded context code should be imported here.
"""

from __future__ import annotations

import dataclasses
import uuid
from collections import deque
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Job descriptor
# ---------------------------------------------------------------------------


def _new_job_id() -> str:
    return str(uuid.uuid4())


def _now_utc() -> datetime:
    return datetime.now(UTC)


@dataclasses.dataclass(frozen=True, eq=False)
class Job:
    """
    An immutable unit of asynchronous work.

    ``job_id`` uniquely identifies this particular job instance.
    ``idempotency_key`` is a stable, caller-supplied key that prevents the
    same logical work unit from being enqueued multiple times (e.g. the same
    document being ingested twice due to a retry at the HTTP layer).

    ``payload`` is a free-form dict of JSON-safe values that carry the data
    the worker needs to execute the job.  The platform does not interpret the
    payload; it is opaque to the queue layer.

    Two ``Job`` instances are considered equal if and only if they share the
    same ``job_id``.  Hash is also derived from ``job_id`` so that jobs can
    be placed in sets and used as dict keys.
    """

    job_id: str = dataclasses.field(default_factory=_new_job_id)
    job_type: str = ""
    idempotency_key: str = ""
    payload: dict[str, object] = dataclasses.field(default_factory=dict)
    created_at: datetime = dataclasses.field(default_factory=_now_utc)
    max_retries: int = 3
    retry_count: int = 0

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("job_id cannot be empty")
        if not self.job_type:
            raise ValueError("job_type cannot be empty")
        if not self.idempotency_key:
            raise ValueError("idempotency_key cannot be empty")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return self.job_id == other.job_id

    def __hash__(self) -> int:
        return hash(self.job_id)


# ---------------------------------------------------------------------------
# Abstract JobQueue interface
# ---------------------------------------------------------------------------


class JobQueue:
    """
    Abstract interface for the platform job queue.

    Workers call ``dequeue`` to claim the next available job, process it,
    then call ``acknowledge`` on success or ``reject`` on failure.

    Subclasses MUST override all methods.  This base class raises
    ``NotImplementedError`` for all operations so that missing overrides are
    caught at runtime during development.

    Design note: this is a concrete class with ``NotImplementedError``, not an
    ABC.  Using ABC would force mypy to reject ``register_singleton(JobQueue,
    InProcessJobQueue)`` in the container without a ``type: ignore`` comment on
    every callsite.  ``NotImplementedError`` achieves the same safety guarantee
    (missing overrides fail loudly) while keeping container registration clean.
    """

    def enqueue(self, job: Job) -> None:
        """
        Submit a job for asynchronous processing.

        Implementations MUST deduplicate by ``idempotency_key``: if a job
        with the same key is already pending or processing, the new job is
        silently dropped.
        """
        raise NotImplementedError

    def dequeue(self, timeout: float = 0.0) -> Job | None:
        """
        Claim the next available job for processing.

        Returns ``None`` if the queue is empty (for in-process implementations)
        or if the timeout elapses (for broker-backed implementations).

        The returned job transitions to a "processing" state and will not be
        returned by subsequent ``dequeue`` calls until it is acknowledged or
        rejected.

        Args:
            timeout: Seconds to wait for a job.  ``0.0`` returns immediately.
        """
        raise NotImplementedError

    def acknowledge(self, job_id: str) -> None:
        """
        Mark a job as successfully completed.

        Releases the idempotency key so the same logical job can be
        re-enqueued in future.  Acknowledging an unknown ``job_id`` is a
        no-op.
        """
        raise NotImplementedError

    def reject(self, job_id: str, requeue: bool = True) -> None:
        """
        Mark a job as failed.

        If ``requeue`` is ``True`` and ``job.retry_count < job.max_retries``,
        the job is re-enqueued with an incremented ``retry_count``.  If retries
        are exhausted or ``requeue`` is ``False``, the job is discarded and
        its idempotency key is released.

        Rejecting an unknown ``job_id`` is a no-op.
        """
        raise NotImplementedError

    def pending_count(self) -> int:
        """Return the number of jobs waiting to be dequeued."""
        raise NotImplementedError

    def processing_count(self) -> int:
        """Return the number of jobs currently claimed by workers."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# In-process implementation
# ---------------------------------------------------------------------------


class InProcessJobQueue(JobQueue):
    """
    Synchronous, in-memory ``JobQueue`` implementation.

    Jobs are stored in a ``deque``; dequeue is FIFO.  Retried jobs are
    placed at the head of the queue so they are attempted before new work.

    Idempotency is enforced via an internal ``set`` of active idempotency
    keys.  A key is "active" from the moment a job is enqueued until the
    moment it is acknowledged (success) or exhausts its retries (failure).
    During this window, calling ``enqueue`` with the same key is a no-op.

    Thread-safety: not guaranteed.  Intended for single-threaded test suites
    and local development.  Production deployments should register a
    broker-backed implementation.
    """

    def __init__(self) -> None:
        self._pending: deque[Job] = deque()
        self._processing: dict[str, Job] = {}
        self._active_idempotency_keys: set[str] = set()

    def enqueue(self, job: Job) -> None:
        if job.idempotency_key in self._active_idempotency_keys:
            return
        self._active_idempotency_keys.add(job.idempotency_key)
        self._pending.append(job)

    def dequeue(self, timeout: float = 0.0) -> Job | None:
        if not self._pending:
            return None
        job = self._pending.popleft()
        self._processing[job.job_id] = job
        return job

    def acknowledge(self, job_id: str) -> None:
        job = self._processing.pop(job_id, None)
        if job is not None:
            self._active_idempotency_keys.discard(job.idempotency_key)

    def reject(self, job_id: str, requeue: bool = True) -> None:
        job = self._processing.pop(job_id, None)
        if job is None:
            return
        if requeue and job.retry_count < job.max_retries:
            # Job is frozen, so create a new instance with the incremented counter.
            retry_job = dataclasses.replace(job, retry_count=job.retry_count + 1)
            self._pending.appendleft(retry_job)
        else:
            self._active_idempotency_keys.discard(job.idempotency_key)

    def pending_count(self) -> int:
        return len(self._pending)

    def processing_count(self) -> int:
        return len(self._processing)

    def clear(self) -> None:
        """Discard all pending and processing jobs. Useful between test cases."""
        self._pending.clear()
        self._processing.clear()
        self._active_idempotency_keys.clear()
