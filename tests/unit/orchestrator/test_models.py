"""Unit tests for mil.orchestrator.models — WorkflowRun, WorkflowStep, enums."""

from __future__ import annotations

from uuid import uuid4

import pytest

from mil.kernel.errors import ConflictError, ValidationError
from mil.orchestrator.models import (
    PinnedVersions,
    StepStatus,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pinned() -> PinnedVersions:
    return PinnedVersions(
        policy="1.2.0",
        extraction="extract-v1",
        inference="model-v3",
        prompt="prompt-v2",
    )


def _make_run(**overrides: object) -> WorkflowRun:
    kwargs: dict[str, object] = {
        "tenant_id": uuid4(),
        "application_id": uuid4(),
        "workflow_type": "DOCUMENT_INGESTION",
        "idempotency_key": "DOCUMENT_INGESTION:doc-123",
        "correlation_id": "corr-abc",
        "pinned_versions": _pinned(),
    }
    kwargs.update(overrides)
    return WorkflowRun.create(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class TestEnumerations:
    def test_workflow_status_values(self) -> None:
        assert set(WorkflowStatus) == {
            WorkflowStatus.PENDING,
            WorkflowStatus.RUNNING,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
        }

    def test_step_status_values(self) -> None:
        assert set(StepStatus) == {
            StepStatus.PENDING,
            StepStatus.IN_PROGRESS,
            StepStatus.COMPLETED,
            StepStatus.FAILED,
        }


# ---------------------------------------------------------------------------
# PinnedVersions value object
# ---------------------------------------------------------------------------


class TestPinnedVersions:
    def test_holds_all_four_dimensions(self) -> None:
        pv = _pinned()
        assert pv.policy == "1.2.0"
        assert pv.extraction == "extract-v1"
        assert pv.inference == "model-v3"
        assert pv.prompt == "prompt-v2"

    def test_is_frozen(self) -> None:
        pv = _pinned()
        with pytest.raises(Exception):  # noqa: B017 - frozen dataclass raises FrozenInstanceError
            pv.policy = "9.9.9"  # type: ignore[misc]

    @pytest.mark.parametrize("field", ["policy", "extraction", "inference", "prompt"])
    def test_empty_dimension_rejected(self, field: str) -> None:
        kwargs = {
            "policy": "1.0.0",
            "extraction": "e",
            "inference": "m",
            "prompt": "p",
            field: "  ",
        }
        with pytest.raises(ValidationError):
            PinnedVersions(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# WorkflowRun.create + version pinning
# ---------------------------------------------------------------------------


class TestWorkflowRunCreate:
    def test_starts_in_pending_state(self) -> None:
        run = _make_run()
        assert run.status == WorkflowStatus.PENDING

    def test_assigns_id(self) -> None:
        run = _make_run()
        assert run.id is not None

    def test_records_correlation_id(self) -> None:
        run = _make_run(correlation_id="corr-xyz")
        assert run.correlation_id == "corr-xyz"

    def test_records_idempotency_key(self) -> None:
        run = _make_run(idempotency_key="DOCUMENT_INGESTION:doc-9")
        assert run.idempotency_key == "DOCUMENT_INGESTION:doc-9"

    def test_pins_all_four_versions(self) -> None:
        run = _make_run()
        assert run.pinned_policy_version == "1.2.0"
        assert run.pinned_extraction_version == "extract-v1"
        assert run.pinned_inference_version == "model-v3"
        assert run.pinned_prompt_version == "prompt-v2"

    def test_pinned_versions_property_roundtrip(self) -> None:
        run = _make_run()
        assert run.pinned_versions == _pinned()

    def test_timestamps_set(self) -> None:
        run = _make_run()
        assert run.created_at is not None
        assert run.updated_at is not None
        assert run.completed_at is None

    def test_empty_workflow_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_run(workflow_type="  ")

    def test_empty_idempotency_key_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_run(idempotency_key="")

    def test_empty_correlation_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_run(correlation_id="")


# ---------------------------------------------------------------------------
# Step planning
# ---------------------------------------------------------------------------


class TestPlanStep:
    def test_plan_step_appends_step(self) -> None:
        run = _make_run()
        run.plan_step(step_name="OCR", step_order=0)
        assert len(run.steps) == 1

    def test_planned_step_is_pending(self) -> None:
        run = _make_run()
        step = run.plan_step(step_name="OCR", step_order=0)
        assert step.status == StepStatus.PENDING

    def test_planned_step_links_to_run(self) -> None:
        run = _make_run()
        step = run.plan_step(step_name="OCR", step_order=0)
        assert step.workflow_run_id == run.id

    def test_planned_step_records_order(self) -> None:
        run = _make_run()
        step = run.plan_step(step_name="EXTRACTION", step_order=1)
        assert step.step_order == 1

    def test_planned_step_default_retry_metadata(self) -> None:
        run = _make_run()
        step = run.plan_step(step_name="OCR", step_order=0)
        assert step.retry_count == 0
        assert step.max_retries == 3

    def test_planned_step_custom_max_retries(self) -> None:
        run = _make_run()
        step = run.plan_step(step_name="OCR", step_order=0, max_retries=5)
        assert step.max_retries == 5

    def test_multiple_steps_preserve_order(self) -> None:
        run = _make_run()
        run.plan_step(step_name="OCR", step_order=0)
        run.plan_step(step_name="EXTRACTION", step_order=1)
        assert [s.step_name for s in run.steps] == ["OCR", "EXTRACTION"]

    def test_empty_step_name_rejected(self) -> None:
        run = _make_run()
        with pytest.raises(ValidationError):
            run.plan_step(step_name="  ", step_order=0)

    def test_negative_step_order_rejected(self) -> None:
        run = _make_run()
        with pytest.raises(ValidationError):
            run.plan_step(step_name="OCR", step_order=-1)


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_mark_running(self) -> None:
        run = _make_run()
        run.mark_running()
        assert run.status == WorkflowStatus.RUNNING

    def test_mark_running_twice_rejected(self) -> None:
        run = _make_run()
        run.mark_running()
        with pytest.raises(ConflictError):
            run.mark_running()

    def test_mark_completed_from_running(self) -> None:
        run = _make_run()
        run.mark_running()
        run.mark_completed()
        assert run.status == WorkflowStatus.COMPLETED
        assert run.completed_at is not None

    def test_mark_completed_from_pending(self) -> None:
        run = _make_run()
        run.mark_completed()
        assert run.status == WorkflowStatus.COMPLETED

    def test_mark_failed(self) -> None:
        run = _make_run()
        run.mark_running()
        run.mark_failed()
        assert run.status == WorkflowStatus.FAILED
        assert run.completed_at is not None

    def test_cannot_fail_completed_run(self) -> None:
        run = _make_run()
        run.mark_completed()
        with pytest.raises(ConflictError):
            run.mark_failed()

    def test_cannot_complete_failed_run(self) -> None:
        run = _make_run()
        run.mark_failed()
        with pytest.raises(ConflictError):
            run.mark_completed()

    def test_is_terminal(self) -> None:
        run = _make_run()
        assert run.is_terminal is False
        run.mark_completed()
        assert run.is_terminal is True


# ---------------------------------------------------------------------------
# ORM metadata
# ---------------------------------------------------------------------------


class TestOrmMetadata:
    def test_workflow_run_table_in_orchestrator_schema(self) -> None:
        assert WorkflowRun.__table__.schema == "orchestrator"

    def test_workflow_step_table_in_orchestrator_schema(self) -> None:
        assert WorkflowStep.__table__.schema == "orchestrator"

    def test_idempotency_key_unique_constraint_present(self) -> None:
        constraint_names = {c.name for c in WorkflowRun.__table__.constraints}
        assert "uq_workflow_runs_idempotency_key" in constraint_names

    def test_step_run_name_unique_constraint_present(self) -> None:
        constraint_names = {c.name for c in WorkflowStep.__table__.constraints}
        assert "uq_workflow_steps_run_step" in constraint_names
