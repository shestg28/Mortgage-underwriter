"""Unit tests for workers.bootstrap — worker startup and per-job execution."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mil.kernel.context import get_request_context
from mil.kernel.job_queue import InProcessJobQueue, Job, JobQueue
from workers.bootstrap import WorkerContext, build_worker_context, process_next

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(correlation_id: str = "corr-1") -> Job:
    return Job(
        job_type="workflow_step",
        idempotency_key=f"run:{correlation_id}:OCR",
        payload={"correlation_id": correlation_id, "step_name": "OCR"},
    )


def _make_context(queue: JobQueue | None = None) -> tuple[WorkerContext, MagicMock]:
    session = MagicMock()
    session_factory = MagicMock(return_value=session)
    ctx = WorkerContext(
        container=MagicMock(),
        session_factory=session_factory,
        job_queue=queue if queue is not None else InProcessJobQueue(),
    )
    return ctx, session


# ---------------------------------------------------------------------------
# build_worker_context
# ---------------------------------------------------------------------------


class TestBuildWorkerContext:
    def test_resolves_job_queue_from_container(self) -> None:
        queue = InProcessJobQueue()
        container = MagicMock()
        container.resolve.return_value = queue
        ctx = build_worker_context(
            settings=MagicMock(),
            container=container,
            session_factory=MagicMock(),
        )
        assert ctx.job_queue is queue
        container.resolve.assert_called_once_with(JobQueue)

    def test_uses_injected_session_factory(self) -> None:
        factory = MagicMock()
        container = MagicMock()
        container.resolve.return_value = InProcessJobQueue()
        ctx = build_worker_context(
            settings=MagicMock(),
            container=container,
            session_factory=factory,
        )
        assert ctx.session_factory is factory

    def test_uses_injected_container(self) -> None:
        container = MagicMock()
        container.resolve.return_value = InProcessJobQueue()
        ctx = build_worker_context(
            settings=MagicMock(),
            container=container,
            session_factory=MagicMock(),
        )
        assert ctx.container is container


# ---------------------------------------------------------------------------
# process_next — empty queue
# ---------------------------------------------------------------------------


class TestProcessNextEmpty:
    def test_returns_false_when_queue_empty(self) -> None:
        ctx, _ = _make_context()
        handler = MagicMock()
        assert process_next(ctx, handler) is False

    def test_handler_not_called_when_queue_empty(self) -> None:
        ctx, _ = _make_context()
        handler = MagicMock()
        process_next(ctx, handler)
        handler.assert_not_called()


# ---------------------------------------------------------------------------
# process_next — success path (Unit of Work)
# ---------------------------------------------------------------------------


class TestProcessNextSuccess:
    def test_returns_true(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, _ = _make_context(queue)
        assert process_next(ctx, MagicMock()) is True

    def test_handler_invoked_with_session_and_job(self) -> None:
        queue = InProcessJobQueue()
        job = _make_job()
        queue.enqueue(job)
        ctx, session = _make_context(queue)
        handler = MagicMock()
        process_next(ctx, handler)
        handler.assert_called_once()
        called_session, called_job = handler.call_args.args
        assert called_session is session
        assert called_job.job_id == job.job_id

    def test_commits_on_success(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, session = _make_context(queue)
        process_next(ctx, MagicMock())
        session.commit.assert_called_once()

    def test_acknowledges_job_on_success(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, _ = _make_context(queue)
        process_next(ctx, MagicMock())
        assert queue.pending_count() == 0
        assert queue.processing_count() == 0

    def test_closes_session(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, session = _make_context(queue)
        process_next(ctx, MagicMock())
        session.close.assert_called_once()

    def test_correlation_id_bound_during_handler(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job(correlation_id="corr-bound"))
        ctx, _ = _make_context(queue)
        seen: list[str] = []

        def handler(session: object, job: object) -> None:
            seen.append(get_request_context().correlation_id)

        process_next(ctx, handler)
        assert seen == ["corr-bound"]


# ---------------------------------------------------------------------------
# process_next — failure path
# ---------------------------------------------------------------------------


class TestProcessNextFailure:
    def test_rolls_back_on_handler_error(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, session = _make_context(queue)

        def handler(session: object, job: object) -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            process_next(ctx, handler)
        session.rollback.assert_called_once()

    def test_does_not_commit_on_error(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, session = _make_context(queue)

        def handler(session: object, job: object) -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            process_next(ctx, handler)
        session.commit.assert_not_called()

    def test_requeues_job_on_error(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, _ = _make_context(queue)

        def handler(session: object, job: object) -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            process_next(ctx, handler)
        # Rejected with requeue (retry_count < max_retries) → back to pending.
        assert queue.pending_count() == 1

    def test_closes_session_on_error(self) -> None:
        queue = InProcessJobQueue()
        queue.enqueue(_make_job())
        ctx, session = _make_context(queue)

        def handler(session: object, job: object) -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            process_next(ctx, handler)
        session.close.assert_called_once()
