"""Unit tests for mil.orchestrator.service — IntelligenceOrchestrator.

The orchestrator is a traffic controller. These tests assert that it
coordinates (creates runs, plans steps, persists outbox events, enqueues jobs)
and that it does so deterministically, idempotently, with versions pinned and
the correlation id propagated to every artefact.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from mil.kernel.events import WorkflowStarted
from mil.kernel.job_queue import InProcessJobQueue
from mil.orchestrator.models import PinnedVersions, WorkflowRun, WorkflowStatus
from mil.orchestrator.service import IntelligenceOrchestrator

# ---------------------------------------------------------------------------
# In-memory fakes (no database, no broker)
# ---------------------------------------------------------------------------


class FakeWorkflowRepository:
    def __init__(self) -> None:
        self.saved: list[WorkflowRun] = []
        self._by_key: dict[str, WorkflowRun] = {}

    def save(self, run: WorkflowRun) -> None:
        self.saved.append(run)
        self._by_key[run.idempotency_key] = run

    def get_by_idempotency_key(self, idempotency_key: str) -> WorkflowRun | None:
        return self._by_key.get(idempotency_key)

    def seed(self, run: WorkflowRun) -> None:
        self._by_key[run.idempotency_key] = run


class FakeOutboxRepository:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, event: object) -> object:
        self.added.append(event)
        return event


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _pinned() -> PinnedVersions:
    return PinnedVersions(policy="1.2.0", extraction="e1", inference="m1", prompt="p1")


def _make_orchestrator() -> tuple[
    IntelligenceOrchestrator, FakeWorkflowRepository, FakeOutboxRepository, InProcessJobQueue
]:
    runs = FakeWorkflowRepository()
    outbox = FakeOutboxRepository()
    queue = InProcessJobQueue()
    orch = IntelligenceOrchestrator(runs, outbox, queue)  # type: ignore[arg-type]
    return orch, runs, outbox, queue


def _start(orch: IntelligenceOrchestrator, **overrides: object) -> WorkflowRun:
    kwargs: dict[str, object] = {
        "tenant_id": uuid4(),
        "application_id": uuid4(),
        "workflow_type": "DOCUMENT_INGESTION",
        "idempotency_key": f"DOCUMENT_INGESTION:{uuid4()}",
        "step_names": ["OCR", "EXTRACTION"],
        "pinned_versions": _pinned(),
    }
    kwargs.update(overrides)
    return orch.start_workflow(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Workflow creation
# ---------------------------------------------------------------------------


class TestStartWorkflowCreatesRun:
    def test_returns_workflow_run(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch)
        assert isinstance(run, WorkflowRun)

    def test_run_is_saved(self) -> None:
        orch, runs, _, _ = _make_orchestrator()
        run = _start(orch)
        assert run in runs.saved

    def test_run_is_running_after_start(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch)
        assert run.status == WorkflowStatus.RUNNING

    def test_plans_all_steps_in_order(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch, step_names=["OCR", "EXTRACTION", "DONE"])
        assert [s.step_name for s in run.steps] == ["OCR", "EXTRACTION", "DONE"]

    def test_empty_step_names_rejected(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        from mil.kernel.errors import ValidationError

        with pytest.raises(ValidationError):
            _start(orch, step_names=[])


# ---------------------------------------------------------------------------
# Version pinning
# ---------------------------------------------------------------------------


class TestVersionPinning:
    def test_pins_versions_on_run(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch)
        assert run.pinned_versions == _pinned()

    def test_individual_pinned_columns(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch)
        assert run.pinned_policy_version == "1.2.0"
        assert run.pinned_extraction_version == "e1"
        assert run.pinned_inference_version == "m1"
        assert run.pinned_prompt_version == "p1"


# ---------------------------------------------------------------------------
# Outbox persistence
# ---------------------------------------------------------------------------


class TestOutboxPersistence:
    def test_persists_one_outbox_event(self) -> None:
        orch, _, outbox, _ = _make_orchestrator()
        _start(orch)
        assert len(outbox.added) == 1

    def test_outbox_event_is_workflow_started(self) -> None:
        orch, _, outbox, _ = _make_orchestrator()
        _start(orch)
        assert isinstance(outbox.added[0], WorkflowStarted)

    def test_outbox_event_references_run(self) -> None:
        orch, _, outbox, _ = _make_orchestrator()
        run = _start(orch)
        event = outbox.added[0]
        assert isinstance(event, WorkflowStarted)
        assert event.workflow_run_id == run.id


# ---------------------------------------------------------------------------
# Job enqueue
# ---------------------------------------------------------------------------


class TestJobEnqueue:
    def test_enqueues_one_job(self) -> None:
        orch, _, _, queue = _make_orchestrator()
        _start(orch)
        assert queue.pending_count() == 1

    def test_job_targets_first_step(self) -> None:
        orch, _, _, queue = _make_orchestrator()
        _start(orch, step_names=["OCR", "EXTRACTION"])
        job = queue.dequeue()
        assert job is not None
        assert job.payload["step_name"] == "OCR"

    def test_job_idempotency_key_is_deterministic(self) -> None:
        orch, _, _, queue = _make_orchestrator()
        run = _start(orch)
        job = queue.dequeue()
        assert job is not None
        assert job.idempotency_key == f"{run.id}:OCR"


# ---------------------------------------------------------------------------
# Correlation propagation
# ---------------------------------------------------------------------------


class TestCorrelationPropagation:
    def test_explicit_correlation_id_on_run(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch, correlation_id="corr-fixed")
        assert run.correlation_id == "corr-fixed"

    def test_correlation_id_on_outbox_event(self) -> None:
        orch, _, outbox, _ = _make_orchestrator()
        _start(orch, correlation_id="corr-fixed")
        event = outbox.added[0]
        assert isinstance(event, WorkflowStarted)
        assert event.correlation_id == "corr-fixed"

    def test_correlation_id_on_job(self) -> None:
        orch, _, _, queue = _make_orchestrator()
        _start(orch, correlation_id="corr-fixed")
        job = queue.dequeue()
        assert job is not None
        assert job.payload["correlation_id"] == "corr-fixed"

    def test_correlation_id_consistent_across_all_artefacts(self) -> None:
        orch, _runs, outbox, queue = _make_orchestrator()
        run = _start(orch, correlation_id="corr-shared")
        event = outbox.added[0]
        job = queue.dequeue()
        assert isinstance(event, WorkflowStarted)
        assert job is not None
        assert run.correlation_id == "corr-shared"
        assert event.correlation_id == "corr-shared"
        assert job.payload["correlation_id"] == "corr-shared"

    def test_correlation_id_autogenerated_when_omitted(self) -> None:
        orch, _, _, _ = _make_orchestrator()
        run = _start(orch, correlation_id=None)
        assert run.correlation_id  # non-empty generated value


# ---------------------------------------------------------------------------
# Idempotency / replay
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_repeat_trigger_returns_existing_run(self) -> None:
        orch, runs, _, _ = _make_orchestrator()
        existing = WorkflowRun.create(
            tenant_id=uuid4(),
            application_id=uuid4(),
            workflow_type="DOCUMENT_INGESTION",
            idempotency_key="DOCUMENT_INGESTION:dup",
            correlation_id="corr-existing",
            pinned_versions=_pinned(),
        )
        runs.seed(existing)
        result = _start(orch, idempotency_key="DOCUMENT_INGESTION:dup")
        assert result is existing

    def test_repeat_trigger_creates_no_new_run(self) -> None:
        orch, runs, _, _ = _make_orchestrator()
        existing = WorkflowRun.create(
            tenant_id=uuid4(),
            application_id=uuid4(),
            workflow_type="DOCUMENT_INGESTION",
            idempotency_key="DOCUMENT_INGESTION:dup",
            correlation_id="corr-existing",
            pinned_versions=_pinned(),
        )
        runs.seed(existing)
        _start(orch, idempotency_key="DOCUMENT_INGESTION:dup")
        assert runs.saved == []

    def test_repeat_trigger_enqueues_no_job(self) -> None:
        orch, runs, _, queue = _make_orchestrator()
        existing = WorkflowRun.create(
            tenant_id=uuid4(),
            application_id=uuid4(),
            workflow_type="DOCUMENT_INGESTION",
            idempotency_key="DOCUMENT_INGESTION:dup",
            correlation_id="corr-existing",
            pinned_versions=_pinned(),
        )
        runs.seed(existing)
        _start(orch, idempotency_key="DOCUMENT_INGESTION:dup")
        assert queue.pending_count() == 0

    def test_repeat_trigger_persists_no_outbox_event(self) -> None:
        orch, runs, outbox, _ = _make_orchestrator()
        existing = WorkflowRun.create(
            tenant_id=uuid4(),
            application_id=uuid4(),
            workflow_type="DOCUMENT_INGESTION",
            idempotency_key="DOCUMENT_INGESTION:dup",
            correlation_id="corr-existing",
            pinned_versions=_pinned(),
        )
        runs.seed(existing)
        _start(orch, idempotency_key="DOCUMENT_INGESTION:dup")
        assert outbox.added == []


# ---------------------------------------------------------------------------
# Coordination-only guarantee
# ---------------------------------------------------------------------------


class TestCoordinationOnly:
    def test_orchestrator_has_no_provider_dependencies(self) -> None:
        """The orchestrator must depend only on coordination collaborators."""
        orch, _, _, _ = _make_orchestrator()
        # The orchestrator holds exactly three collaborators: workflow repo,
        # outbox repo, and job queue. No provider, OCR, AI, policy, or evidence
        # dependency exists.
        attrs = {k for k in vars(orch) if not k.startswith("__")}
        assert attrs == {"_runs", "_outbox", "_queue"}
