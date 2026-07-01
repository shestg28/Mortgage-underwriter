"""
Retry policy primitives for the Intelligence Pipeline (ADR-008).

This module provides the *decision* and *extension points* for retrying failed
pipeline work. It deliberately does NOT schedule retries against a broker —
broker scheduling is a deployment concern. Workers use ``RetryPolicy`` to decide
whether a failure is retryable, terminal, or has exhausted its attempts, and the
``BackoffStrategy`` / ``DeadLetterSink`` interfaces are the seams a real
broker-backed scheduler plugs into later.

Classification source of truth (ADR-008): retryability is a property of the
failure, declared at the source. ``ProviderError.retryable`` carries it; the
policy reads that flag rather than hard-coding error lists.

Dependency rule: imports only from ``mil.kernel`` and the Python standard
library. No bounded context business logic is imported.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mil.kernel.job_queue import Job

# ---------------------------------------------------------------------------
# Retry decision
# ---------------------------------------------------------------------------


class RetryDecision(enum.StrEnum):
    """
    The outcome of classifying a failure.

    RETRY             — the failure is transient and attempts remain; the work
                        should be re-attempted (the worker re-raises so its
                        Unit of Work rolls back and the queue requeues).
    RETRIES_EXHAUSTED — the failure is transient but the attempt budget is spent;
                        treat as terminal and route to the dead-letter sink.
    NON_RETRYABLE     — the failure is structural; retrying cannot help. Terminal.
    """

    RETRY = "RETRY"
    RETRIES_EXHAUSTED = "RETRIES_EXHAUSTED"
    NON_RETRYABLE = "NON_RETRYABLE"

    @property
    def is_terminal(self) -> bool:
        """Return ``True`` if the decision ends the work (no further attempts)."""
        return self in {RetryDecision.RETRIES_EXHAUSTED, RetryDecision.NON_RETRYABLE}


def is_retryable(exc: BaseException) -> bool:
    """
    Return whether an exception is retryable.

    Reads the ``retryable`` flag declared at the source (e.g. ``ProviderError``).
    Exceptions that do not declare retryability are treated as non-retryable —
    an unknown failure is not blindly retried.
    """
    return bool(getattr(exc, "retryable", False))


# ---------------------------------------------------------------------------
# Backoff strategy (extension point — not wired to a scheduler in this sprint)
# ---------------------------------------------------------------------------


class BackoffStrategy(ABC):
    """
    Computes the delay before a retry attempt.

    The platform computes the recommended delay here; a broker-backed scheduler
    (a later deployment concern) is responsible for actually deferring the
    redelivery by that amount. In-process development requeues immediately.
    """

    @abstractmethod
    def compute_delay(self, attempt: int) -> float:
        """Return the delay in seconds before retry ``attempt`` (0-based)."""


@dataclass(frozen=True)
class ExponentialBackoff(BackoffStrategy):
    """
    Exponential backoff with a ceiling.

    delay(attempt) = min(base_seconds * (factor ** attempt), max_seconds)
    """

    base_seconds: float = 1.0
    factor: float = 2.0
    max_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.base_seconds < 0:
            raise ValueError("base_seconds cannot be negative")
        if self.factor < 1.0:
            raise ValueError("factor must be >= 1.0")
        if self.max_seconds < self.base_seconds:
            raise ValueError("max_seconds must be >= base_seconds")

    def compute_delay(self, attempt: int) -> float:
        if attempt < 0:
            raise ValueError("attempt cannot be negative")
        return min(self.base_seconds * (self.factor**attempt), self.max_seconds)


# ---------------------------------------------------------------------------
# Dead-letter sink (placeholder — no durable destination in this sprint)
# ---------------------------------------------------------------------------


class DeadLetterSink(ABC):
    """
    Destination for jobs that have permanently failed.

    A production implementation persists the job and its failure for operator
    inspection and replay. This sprint provides the interface only.
    """

    @abstractmethod
    def record(self, job: Job, error: BaseException) -> None:
        """Record a permanently failed job and the error that terminated it."""


class NoOpDeadLetterSink(DeadLetterSink):
    """
    Inert dead-letter sink used until a durable destination is wired.

    Discards the job. The terminal failure is still observable via the
    ``WorkflowStepFailed`` event and the FAILED workflow/document state, so no
    information is lost at the audit level; only the replay convenience is absent.
    """

    def record(self, job: Job, error: BaseException) -> None:
        return None


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetryPolicy:
    """
    Decides how a failure is handled and how long to wait before a retry.

    ``classify`` is the decision used by the worker; ``next_delay`` exposes the
    backoff for a future scheduler. The per-job attempt budget (``max_retries``)
    is supplied by the ``Job`` itself, so a job can carry its own budget; the
    policy's ``default_max_attempts`` is used only when none is supplied.
    """

    default_max_attempts: int = 3
    backoff: BackoffStrategy = field(default_factory=ExponentialBackoff)

    def classify(self, exc: BaseException, *, retry_count: int, max_retries: int) -> RetryDecision:
        """
        Classify a failure given how many attempts have already been made.

        Args:
            exc:         The exception that failed the work.
            retry_count: Attempts already made (0 on the first try).
            max_retries: The attempt budget for this job.
        """
        if not is_retryable(exc):
            return RetryDecision.NON_RETRYABLE
        if retry_count >= max_retries:
            return RetryDecision.RETRIES_EXHAUSTED
        return RetryDecision.RETRY

    def next_delay(self, retry_count: int) -> float:
        """Return the recommended delay before the next attempt."""
        return self.backoff.compute_delay(retry_count)
