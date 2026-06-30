"""
ORM models and domain types for the Intelligence Orchestrator bounded context.

The orchestrator coordinates multi-step intelligence workflows. It owns *workflow
state* only — never business logic. It performs no OCR, no extraction, no
evidence creation, no finding generation, and no policy evaluation. Those belong
to their respective bounded contexts (Engineering Constitution, Principle VII;
ARCHITECTURE.md §"Intelligence Orchestrator").

This module defines:

- ``WorkflowStatus`` / ``StepStatus`` — lifecycle enumerations.
- ``PinnedVersions`` — the immutable version set pinned at run creation
  (ADR-009, Principle XII — Deterministic Intelligence).
- ``WorkflowRun`` — one execution of the pipeline; anchors reproducibility
  (pinned versions) and end-to-end tracing (correlation id).
- ``WorkflowStep`` — one named, ordered unit of work within a run, carrying
  retry metadata and error information.

Reproducibility (ADR-009): a run pins its policy, extraction, inference, and
prompt versions at creation. Steps read the pinned set from the run; nothing in
the pipeline reads live configuration mid-run.

Idempotency (ADR-008): a run carries a deterministic ``idempotency_key`` and a
unique constraint enforces that re-triggering the same logical work does not
create a duplicate run. Each step is unique within its run by ``step_name``.

Schema: ``orchestrator`` PostgreSQL schema.

Dependency rule: imports only from ``mil.kernel`` and the Python standard
library. No other bounded context is imported.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mil.kernel.db import Base
from mil.kernel.errors import ConflictError, ValidationError

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class WorkflowStatus(enum.StrEnum):
    """
    Lifecycle state of a ``WorkflowRun``.

    PENDING   — the run has been created and its steps planned, not yet started.
    RUNNING   — the run has started; steps are progressing.
    COMPLETED — every step completed successfully (terminal).
    FAILED    — a step failed terminally after exhausting retries (terminal).
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StepStatus(enum.StrEnum):
    """
    Lifecycle state of a ``WorkflowStep``.

    PENDING     — planned, not yet dispatched/executed.
    IN_PROGRESS — claimed by a worker and executing.
    COMPLETED   — finished successfully (terminal).
    FAILED      — failed terminally after exhausting retries (terminal).
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_TERMINAL_RUN_STATES: frozenset[str] = frozenset({WorkflowStatus.COMPLETED, WorkflowStatus.FAILED})


# ---------------------------------------------------------------------------
# Pinned version set (value object)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PinnedVersions:
    """
    The immutable version set pinned to a ``WorkflowRun`` at creation.

    Per ADR-009 and Principle XII, every workflow run fixes the four attribution
    dimensions at the moment it starts, so its output is reproducible and immune
    to mid-run configuration changes. Steps read these values from the run; they
    never consult live configuration.

    Attributes:
        policy:     Policy Pack version active for the application at run start.
        extraction: Extraction engine version.
        inference:  Inference (AI model) version.
        prompt:     Prompt template version.

    All four are required, non-empty strings. A dimension that is genuinely not
    applicable to a given workflow type is pinned to an explicit sentinel (e.g.
    ``"n/a"``) by the caller — it is never left blank, so the attribution record
    is always complete.
    """

    policy: str
    extraction: str
    inference: str
    prompt: str

    def __post_init__(self) -> None:
        for name, value in (
            ("policy", self.policy),
            ("extraction", self.extraction),
            ("inference", self.inference),
            ("prompt", self.prompt),
        ):
            if not value or not value.strip():
                raise ValidationError(
                    f"Pinned {name} version must not be empty", field=f"pinned_{name}_version"
                )


# ---------------------------------------------------------------------------
# WorkflowStep entity (owned by the WorkflowRun)
# ---------------------------------------------------------------------------


class WorkflowStep(Base):
    """
    One named, ordered unit of work within a ``WorkflowRun``.

    A step is a coordination record — it names a stage in the pipeline and
    tracks that stage's status, retry metadata, and any error information. It
    holds no business logic and no business data; the work itself is performed
    by the relevant bounded context's service when a worker executes the step's
    job (US2 Sprint 2+).

    Idempotency (ADR-008): ``(workflow_run_id, step_name)`` is unique, so a step
    cannot be created twice within a run even under at-least-once delivery.
    """

    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_run_id", "step_name", name="uq_workflow_steps_run_step"),
        {"schema": "orchestrator"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workflow_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("orchestrator.workflow_runs.id"), nullable=False
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=StepStatus.PENDING)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped[WorkflowRun] = relationship("WorkflowRun", back_populates="steps")

    @property
    def status_enum(self) -> StepStatus:
        """Return the current step status as a typed enum value."""
        return StepStatus(self.status)

    def __repr__(self) -> str:
        return (
            f"<WorkflowStep id={self.id} run={self.workflow_run_id} "
            f"name={self.step_name} order={self.step_order} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# WorkflowRun — coordination aggregate
# ---------------------------------------------------------------------------


class WorkflowRun(Base):
    """
    One execution of an intelligence pipeline for a mortgage application.

    The run is the orchestrator's record of coordination. It anchors two
    cross-cutting guarantees:

    - **Reproducibility (ADR-009, Principle XII):** the run pins the policy,
      extraction, inference, and prompt versions at creation. All steps read
      these from the run; nothing reads live configuration mid-run.
    - **Traceability (ADR-009, Principle X):** the run carries a
      ``correlation_id`` that threads through its outbox events, jobs, and
      domain events, enabling single-trace reconstruction of the whole
      execution.

    The run owns its steps. It contains no business logic — it does not perform
    OCR, extraction, evidence creation, finding generation, or policy
    evaluation.

    Identity: ``id`` is the workflow run identifier (the ``WorkflowRunId``).
    ``idempotency_key`` is a deterministic key for the triggering work
    (ADR-008); a unique constraint prevents duplicate runs for the same trigger.
    """

    __tablename__ = "workflow_runs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_workflow_runs_idempotency_key"),
        {"schema": "orchestrator"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("core.applications.id"), nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Deterministic key for the triggering work — unique, prevents duplicate runs.
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    # Threads through outbox events, jobs, and domain events (ADR-009).
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=WorkflowStatus.PENDING)
    # Pinned version set (ADR-009 / Principle XII) — fixed at run creation.
    pinned_policy_version: Mapped[str] = mapped_column(String(100), nullable=False)
    pinned_extraction_version: Mapped[str] = mapped_column(String(100), nullable=False)
    pinned_inference_version: Mapped[str] = mapped_column(String(100), nullable=False)
    pinned_prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    steps: Mapped[list[WorkflowStep]] = relationship(
        "WorkflowStep",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        application_id: UUID,
        workflow_type: str,
        idempotency_key: str,
        correlation_id: str,
        pinned_versions: PinnedVersions,
    ) -> WorkflowRun:
        """
        Create a new workflow run in PENDING state with its versions pinned.

        The version set is fixed here and never changes for the life of the
        run (ADR-009). The ``correlation_id`` is set here and propagated by the
        orchestrator to every outbox event, job, and domain event the run
        produces.

        Args:
            tenant_id:        Institution the run belongs to.
            application_id:   Application the run coordinates.
            workflow_type:    Coordination label (e.g. ``"DOCUMENT_INGESTION"``).
            idempotency_key:  Deterministic key for the triggering work.
            correlation_id:   End-to-end trace identifier for this execution.
            pinned_versions:  The four attribution versions, fixed at creation.
        """
        if not workflow_type or not workflow_type.strip():
            raise ValidationError("workflow_type must not be empty", field="workflow_type")
        if not idempotency_key or not idempotency_key.strip():
            raise ValidationError("idempotency_key must not be empty", field="idempotency_key")
        if not correlation_id or not correlation_id.strip():
            raise ValidationError("correlation_id must not be empty", field="correlation_id")

        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            application_id=application_id,
            workflow_type=workflow_type.strip(),
            idempotency_key=idempotency_key.strip(),
            correlation_id=correlation_id.strip(),
            status=WorkflowStatus.PENDING,
            pinned_policy_version=pinned_versions.policy,
            pinned_extraction_version=pinned_versions.extraction,
            pinned_inference_version=pinned_versions.inference,
            pinned_prompt_version=pinned_versions.prompt,
            created_at=now,
            updated_at=now,
        )

    # ------------------------------------------------------------------
    # Step planning
    # ------------------------------------------------------------------

    def plan_step(self, *, step_name: str, step_order: int, max_retries: int = 3) -> WorkflowStep:
        """
        Add a planned step to this run in PENDING state.

        Steps are coordination records only — naming a stage in the pipeline.
        The orchestrator plans the full ordered sequence at run start; workers
        execute each step's job in a later sprint.

        Raises:
            ValidationError: If ``step_name`` is empty or ``step_order`` negative.
        """
        if not step_name or not step_name.strip():
            raise ValidationError("step_name must not be empty", field="step_name")
        if step_order < 0:
            raise ValidationError("step_order cannot be negative", field="step_order")

        now = datetime.now(UTC)
        step = WorkflowStep(
            id=uuid4(),
            workflow_run_id=self.id,
            step_name=step_name.strip(),
            step_order=step_order,
            status=StepStatus.PENDING,
            retry_count=0,
            max_retries=max_retries,
            created_at=now,
            updated_at=now,
        )
        self.steps.append(step)
        self._touch()
        return step

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def mark_running(self) -> None:
        """Advance from PENDING to RUNNING when the first step is dispatched."""
        if self.status != WorkflowStatus.PENDING:
            raise ConflictError(f"Cannot start a {self.status} workflow run (id={self.id})")
        self.status = WorkflowStatus.RUNNING
        self._touch()

    def mark_completed(self) -> None:
        """Advance to COMPLETED when all steps have finished successfully."""
        if self.status not in {WorkflowStatus.PENDING, WorkflowStatus.RUNNING}:
            raise ConflictError(f"Cannot complete a {self.status} workflow run (id={self.id})")
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self._touch()

    def mark_failed(self) -> None:
        """Transition to FAILED (terminal) when a step fails terminally."""
        if self.status in _TERMINAL_RUN_STATES:
            raise ConflictError(f"Cannot fail a {self.status} workflow run (id={self.id})")
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self._touch()

    # ------------------------------------------------------------------
    # Internals / properties
    # ------------------------------------------------------------------

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @property
    def status_enum(self) -> WorkflowStatus:
        """Return the current run status as a typed enum value."""
        return WorkflowStatus(self.status)

    @property
    def pinned_versions(self) -> PinnedVersions:
        """Return the pinned version set as a value object."""
        return PinnedVersions(
            policy=self.pinned_policy_version,
            extraction=self.pinned_extraction_version,
            inference=self.pinned_inference_version,
            prompt=self.pinned_prompt_version,
        )

    @property
    def is_terminal(self) -> bool:
        """Return ``True`` if the run is in a terminal state."""
        return self.status in _TERMINAL_RUN_STATES

    def __repr__(self) -> str:
        return (
            f"<WorkflowRun id={self.id} type={self.workflow_type} "
            f"status={self.status} corr={self.correlation_id}>"
        )
