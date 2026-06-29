"""Unit tests for mil.kernel.events — domain event definitions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from mil.kernel.events import (
    DocumentIngested,
    DomainEvent,
    EvidenceExtracted,
    FindingGenerated,
    FindingStateChanged,
    OverrideRecorded,
    WorkflowStepFailed,
)
from mil.kernel.types import (
    ApplicationId,
    DocumentId,
    EvidenceItemId,
    FindingId,
    TenantId,
    WorkflowRunId,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_tenant_id() -> TenantId:
    return TenantId(uuid4())


def make_document_ingested(**kwargs: object) -> DocumentIngested:
    defaults: dict[str, object] = {
        "tenant_id": make_tenant_id(),
        "document_id": DocumentId(uuid4()),
        "application_id": ApplicationId(uuid4()),
        "storage_reference": "s3://mil-documents/doc-001",
        "content_hash": "sha256:abc123",
    }
    defaults.update(kwargs)
    return DocumentIngested(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# DomainEvent base — auto-generated fields
# ---------------------------------------------------------------------------


class TestDomainEventBase:
    def test_event_id_is_auto_generated_string(self) -> None:
        event = make_document_ingested()
        assert isinstance(event.event_id, str)
        assert len(event.event_id) == 36  # UUID4 canonical form

    def test_occurred_at_is_utc_datetime(self) -> None:
        event = make_document_ingested()
        assert isinstance(event.occurred_at, datetime)
        assert event.occurred_at.tzinfo is not None

    def test_correlation_id_defaults_to_empty(self) -> None:
        event = make_document_ingested()
        assert event.correlation_id == ""

    def test_correlation_id_can_be_set(self) -> None:
        event = make_document_ingested(correlation_id="corr-001")
        assert event.correlation_id == "corr-001"

    def test_event_id_unique_across_instances(self) -> None:
        a = make_document_ingested()
        b = make_document_ingested()
        assert a.event_id != b.event_id

    def test_custom_event_id_accepted(self) -> None:
        custom_id = "00000000-0000-0000-0000-000000000001"
        event = make_document_ingested(event_id=custom_id)
        assert event.event_id == custom_id

    def test_domain_event_is_abstract_base(self) -> None:
        assert issubclass(DocumentIngested, DomainEvent)


# ---------------------------------------------------------------------------
# DomainEvent.to_dict() serialisation
# ---------------------------------------------------------------------------


class TestDomainEventToDict:
    def test_to_dict_includes_event_type(self) -> None:
        event = make_document_ingested()
        d = event.to_dict()
        assert d["event_type"] == "DocumentIngested"

    def test_to_dict_converts_uuid_fields_to_strings(self) -> None:
        event = make_document_ingested()
        d = event.to_dict()
        assert isinstance(d["tenant_id"], str)
        assert isinstance(d["document_id"], str)
        assert isinstance(d["application_id"], str)

    def test_to_dict_uuid_strings_are_valid(self) -> None:
        event = make_document_ingested()
        d = event.to_dict()
        UUID(str(d["tenant_id"]))  # should not raise

    def test_to_dict_converts_datetime_to_isoformat(self) -> None:
        event = make_document_ingested()
        d = event.to_dict()
        ts = str(d["occurred_at"])
        assert "T" in ts

    def test_to_dict_includes_all_scalar_fields(self) -> None:
        event = make_document_ingested(
            storage_reference="s3://bucket/doc",
            content_hash="sha256:deadbeef",
            document_name="payslip.pdf",
        )
        d = event.to_dict()
        assert d["storage_reference"] == "s3://bucket/doc"
        assert d["content_hash"] == "sha256:deadbeef"
        assert d["document_name"] == "payslip.pdf"


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestDomainEventImmutability:
    def test_event_is_frozen(self) -> None:
        event = make_document_ingested()
        with pytest.raises(FrozenInstanceError):
            event.correlation_id = "mutated"  # type: ignore[misc]

    def test_tenant_id_cannot_be_changed(self) -> None:
        event = make_document_ingested()
        with pytest.raises(FrozenInstanceError):
            event.tenant_id = TenantId(uuid4())  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DocumentIngested
# ---------------------------------------------------------------------------


class TestDocumentIngested:
    def test_create_minimal(self) -> None:
        tenant_id = make_tenant_id()
        doc_id = DocumentId(uuid4())
        app_id = ApplicationId(uuid4())
        event = DocumentIngested(
            tenant_id=tenant_id,
            document_id=doc_id,
            application_id=app_id,
            storage_reference="s3://bucket/file",
            content_hash="sha256:abc",
        )
        assert event.tenant_id == tenant_id
        assert event.document_id == doc_id
        assert event.application_id == app_id
        assert event.document_name == ""

    def test_document_name_optional(self) -> None:
        event = make_document_ingested(document_name="bank_statement.pdf")
        assert event.document_name == "bank_statement.pdf"

    def test_to_dict_event_type(self) -> None:
        event = make_document_ingested()
        assert event.to_dict()["event_type"] == "DocumentIngested"


# ---------------------------------------------------------------------------
# EvidenceExtracted
# ---------------------------------------------------------------------------


class TestEvidenceExtracted:
    def test_create_with_evidence_ids(self) -> None:
        ids = (EvidenceItemId(uuid4()), EvidenceItemId(uuid4()))
        event = EvidenceExtracted(
            tenant_id=make_tenant_id(),
            document_id=DocumentId(uuid4()),
            application_id=ApplicationId(uuid4()),
            evidence_item_ids=ids,
            extraction_version="1.2.3",
        )
        assert len(event.evidence_item_ids) == 2
        assert event.extraction_version == "1.2.3"

    def test_evidence_item_ids_serialised_as_list_of_strings(self) -> None:
        ids = (EvidenceItemId(uuid4()), EvidenceItemId(uuid4()))
        event = EvidenceExtracted(
            tenant_id=make_tenant_id(),
            document_id=DocumentId(uuid4()),
            application_id=ApplicationId(uuid4()),
            evidence_item_ids=ids,
            extraction_version="1.0.0",
        )
        d = event.to_dict()
        assert isinstance(d["evidence_item_ids"], list)
        for item in d["evidence_item_ids"]:  # type: ignore[union-attr]
            UUID(str(item))  # should be valid UUID strings

    def test_empty_evidence_ids_allowed(self) -> None:
        event = EvidenceExtracted(
            tenant_id=make_tenant_id(),
            document_id=DocumentId(uuid4()),
            application_id=ApplicationId(uuid4()),
            evidence_item_ids=(),
            extraction_version="1.0.0",
        )
        assert event.evidence_item_ids == ()


# ---------------------------------------------------------------------------
# FindingGenerated
# ---------------------------------------------------------------------------


class TestFindingGenerated:
    def test_create(self) -> None:
        event = FindingGenerated(
            tenant_id=make_tenant_id(),
            finding_id=FindingId(uuid4()),
            application_id=ApplicationId(uuid4()),
            finding_type="income_verification",
            policy_version="2.1.0",
        )
        assert event.finding_type == "income_verification"
        assert event.policy_version == "2.1.0"

    def test_to_dict_event_type(self) -> None:
        event = FindingGenerated(
            tenant_id=make_tenant_id(),
            finding_id=FindingId(uuid4()),
            application_id=ApplicationId(uuid4()),
            finding_type="property_value",
            policy_version="1.0.0",
        )
        assert event.to_dict()["event_type"] == "FindingGenerated"


# ---------------------------------------------------------------------------
# FindingStateChanged
# ---------------------------------------------------------------------------


class TestFindingStateChanged:
    def test_create(self) -> None:
        event = FindingStateChanged(
            tenant_id=make_tenant_id(),
            finding_id=FindingId(uuid4()),
            application_id=ApplicationId(uuid4()),
            from_state="Extracted",
            to_state="NeedsReview",
        )
        assert event.from_state == "Extracted"
        assert event.to_state == "NeedsReview"
        assert event.changed_by_user_id == ""

    def test_user_id_optional(self) -> None:
        event = FindingStateChanged(
            tenant_id=make_tenant_id(),
            finding_id=FindingId(uuid4()),
            application_id=ApplicationId(uuid4()),
            from_state="NeedsReview",
            to_state="Verified",
            changed_by_user_id="user-001",
        )
        assert event.changed_by_user_id == "user-001"


# ---------------------------------------------------------------------------
# OverrideRecorded
# ---------------------------------------------------------------------------


class TestOverrideRecorded:
    def test_create(self) -> None:
        event = OverrideRecorded(
            tenant_id=make_tenant_id(),
            finding_id=FindingId(uuid4()),
            application_id=ApplicationId(uuid4()),
            reviewer_user_id="reviewer-001",
            override_reason="Supplemental income not captured by AI",
        )
        assert event.reviewer_user_id == "reviewer-001"
        assert event.previous_value == ""
        assert event.new_value == ""

    def test_with_before_after_values(self) -> None:
        event = OverrideRecorded(
            tenant_id=make_tenant_id(),
            finding_id=FindingId(uuid4()),
            application_id=ApplicationId(uuid4()),
            reviewer_user_id="reviewer-001",
            override_reason="Corrected income figure",
            previous_value="45000",
            new_value="52000",
        )
        assert event.previous_value == "45000"
        assert event.new_value == "52000"


# ---------------------------------------------------------------------------
# WorkflowStepFailed
# ---------------------------------------------------------------------------


class TestWorkflowStepFailed:
    def test_create(self) -> None:
        event = WorkflowStepFailed(
            tenant_id=make_tenant_id(),
            workflow_run_id=WorkflowRunId(uuid4()),
            step_name="ocr",
            error_code="PROVIDER_UNAVAILABLE",
            error_message="OCR provider timed out",
        )
        assert event.step_name == "ocr"
        assert event.error_code == "PROVIDER_UNAVAILABLE"
        assert event.retry_count == 0

    def test_retry_count_recorded(self) -> None:
        event = WorkflowStepFailed(
            tenant_id=make_tenant_id(),
            workflow_run_id=WorkflowRunId(uuid4()),
            step_name="extraction",
            error_code="PROVIDER_UNAVAILABLE",
            error_message="Extraction failed",
            retry_count=3,
        )
        assert event.retry_count == 3


# ---------------------------------------------------------------------------
# Equality and identity
# ---------------------------------------------------------------------------


class TestDomainEventEquality:
    def test_same_event_id_equals(self) -> None:
        event_id = "test-event-id-001"
        a = make_document_ingested(event_id=event_id)
        b = make_document_ingested(event_id=event_id)
        assert a == b

    def test_different_event_ids_not_equal(self) -> None:
        a = make_document_ingested()
        b = make_document_ingested()
        assert a != b

    def test_occurred_at_auto_generated_near_now(self) -> None:
        before = datetime.now(UTC)
        event = make_document_ingested()
        after = datetime.now(UTC)
        assert before <= event.occurred_at <= after
