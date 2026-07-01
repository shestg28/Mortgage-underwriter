"""Unit tests for mil.orchestrator.retry — retry policy and extension points."""

from __future__ import annotations

import pytest

from mil.kernel.errors import ProviderError, ProviderVersionMissingError
from mil.kernel.job_queue import Job
from mil.orchestrator.retry import (
    ExponentialBackoff,
    NoOpDeadLetterSink,
    RetryDecision,
    RetryPolicy,
    is_retryable,
)

# ---------------------------------------------------------------------------
# is_retryable
# ---------------------------------------------------------------------------


class TestIsRetryable:
    def test_generic_provider_error_is_retryable(self) -> None:
        assert is_retryable(ProviderError("temporary outage")) is True

    def test_explicit_non_retryable_provider_error(self) -> None:
        assert is_retryable(ProviderError("bad input", retryable=False)) is False

    def test_version_missing_is_terminal(self) -> None:
        assert is_retryable(ProviderVersionMissingError("OCRProvider", "provider_version")) is False

    def test_unknown_exception_not_retryable(self) -> None:
        assert is_retryable(ValueError("boom")) is False


# ---------------------------------------------------------------------------
# RetryPolicy.classify
# ---------------------------------------------------------------------------


class TestClassify:
    def test_retryable_with_attempts_remaining_retries(self) -> None:
        policy = RetryPolicy()
        decision = policy.classify(ProviderError("x"), retry_count=0, max_retries=3)
        assert decision is RetryDecision.RETRY

    def test_retryable_at_budget_is_exhausted(self) -> None:
        policy = RetryPolicy()
        decision = policy.classify(ProviderError("x"), retry_count=3, max_retries=3)
        assert decision is RetryDecision.RETRIES_EXHAUSTED

    def test_retryable_over_budget_is_exhausted(self) -> None:
        policy = RetryPolicy()
        decision = policy.classify(ProviderError("x"), retry_count=5, max_retries=3)
        assert decision is RetryDecision.RETRIES_EXHAUSTED

    def test_non_retryable_is_non_retryable(self) -> None:
        policy = RetryPolicy()
        decision = policy.classify(
            ProviderVersionMissingError("p", "v"), retry_count=0, max_retries=3
        )
        assert decision is RetryDecision.NON_RETRYABLE

    def test_retry_decision_is_not_terminal(self) -> None:
        assert RetryDecision.RETRY.is_terminal is False

    def test_exhausted_decision_is_terminal(self) -> None:
        assert RetryDecision.RETRIES_EXHAUSTED.is_terminal is True

    def test_non_retryable_decision_is_terminal(self) -> None:
        assert RetryDecision.NON_RETRYABLE.is_terminal is True


# ---------------------------------------------------------------------------
# ExponentialBackoff
# ---------------------------------------------------------------------------


class TestExponentialBackoff:
    def test_first_attempt_is_base(self) -> None:
        backoff = ExponentialBackoff(base_seconds=1.0, factor=2.0, max_seconds=60.0)
        assert backoff.compute_delay(0) == 1.0

    def test_grows_exponentially(self) -> None:
        backoff = ExponentialBackoff(base_seconds=1.0, factor=2.0, max_seconds=60.0)
        assert backoff.compute_delay(1) == 2.0
        assert backoff.compute_delay(2) == 4.0
        assert backoff.compute_delay(3) == 8.0

    def test_respects_ceiling(self) -> None:
        backoff = ExponentialBackoff(base_seconds=1.0, factor=2.0, max_seconds=5.0)
        assert backoff.compute_delay(10) == 5.0

    def test_negative_attempt_rejected(self) -> None:
        with pytest.raises(ValueError):
            ExponentialBackoff().compute_delay(-1)

    def test_invalid_factor_rejected(self) -> None:
        with pytest.raises(ValueError):
            ExponentialBackoff(factor=0.5)

    def test_policy_next_delay_uses_backoff(self) -> None:
        policy = RetryPolicy(backoff=ExponentialBackoff(base_seconds=2.0))
        assert policy.next_delay(0) == 2.0


# ---------------------------------------------------------------------------
# NoOpDeadLetterSink
# ---------------------------------------------------------------------------


class TestNoOpDeadLetterSink:
    def test_record_is_noop(self) -> None:
        sink = NoOpDeadLetterSink()
        job = Job(job_type="t", idempotency_key="k")
        # Must not raise; returns None.
        assert sink.record(job, ProviderError("x")) is None
