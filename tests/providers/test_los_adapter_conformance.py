"""
LOSAdapter conformance tests.

Verifies that any concrete ``LOSAdapter`` satisfies the interface contract
defined in ``mil.kernel.providers.los_adapter``.

Engineering Constitution Principle VI (API-First Integration): MIL must remain
vendor-agnostic.  The adapter translates LOS-specific data to MIL's domain
model without leaking LOS details into the core platform.
"""

from __future__ import annotations

import pytest

from mil.kernel.providers.los_adapter import (
    ApplicationData,
    DocumentReference,
    LOSAdapter,
    ReadinessStatus,
)


class TestLOSAdapterInterfaceContract:
    """Verify the abstract interface structure."""

    def test_los_adapter_is_abstract(self) -> None:
        assert LOSAdapter.__abstractmethods__ != set()

    def test_read_application_is_abstract(self) -> None:
        assert "read_application" in LOSAdapter.__abstractmethods__

    def test_read_documents_is_abstract(self) -> None:
        assert "read_documents" in LOSAdapter.__abstractmethods__

    def test_notify_readiness_is_abstract(self) -> None:
        assert "notify_readiness" in LOSAdapter.__abstractmethods__

    def test_concrete_adapter_is_subclass(self, los_adapter: LOSAdapter) -> None:
        assert isinstance(los_adapter, LOSAdapter)


class TestReadApplication:
    """read_application() must return a valid ApplicationData."""

    def test_returns_application_data(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_application("LOS-REF-001")
        assert isinstance(result, ApplicationData)

    def test_los_reference_echoed(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_application("LOS-REF-001")
        assert result.los_reference == "LOS-REF-001"

    def test_application_type_is_non_empty(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_application("LOS-REF-001")
        assert isinstance(result.application_type, str)
        assert result.application_type != ""

    def test_metadata_is_dict(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_application("LOS-REF-001")
        assert isinstance(result.metadata, dict)

    def test_different_references_return_distinct_objects(self, los_adapter: LOSAdapter) -> None:
        a = los_adapter.read_application("LOS-001")
        b = los_adapter.read_application("LOS-002")
        assert a.los_reference != b.los_reference


class TestReadDocuments:
    """read_documents() must return a list of DocumentReference objects."""

    def test_returns_list(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_documents("LOS-REF-001")
        assert isinstance(result, list)

    def test_all_items_are_document_references(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_documents("LOS-REF-001")
        for item in result:
            assert isinstance(item, DocumentReference)

    def test_each_reference_has_los_reference(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_documents("LOS-REF-001")
        for doc in result:
            assert doc.los_reference != ""

    def test_each_reference_has_document_name(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_documents("LOS-REF-001")
        for doc in result:
            assert isinstance(doc.document_name, str)

    def test_each_reference_has_document_type(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_documents("LOS-REF-001")
        for doc in result:
            assert doc.document_type != ""

    def test_content_url_is_string_or_none(self, los_adapter: LOSAdapter) -> None:
        result = los_adapter.read_documents("LOS-REF-001")
        for doc in result:
            assert doc.content_url is None or isinstance(doc.content_url, str)


class TestNotifyReadiness:
    """notify_readiness() must accept a ReadinessStatus and not raise."""

    def test_notify_ready_status(self, los_adapter: LOSAdapter) -> None:
        status = ReadinessStatus(
            los_reference="LOS-REF-001",
            is_ready=True,
            summary="Application is ready for underwriting.",
        )
        los_adapter.notify_readiness("LOS-REF-001", status)  # must not raise

    def test_notify_not_ready_status(self, los_adapter: LOSAdapter) -> None:
        status = ReadinessStatus(
            los_reference="LOS-REF-001",
            is_ready=False,
            summary="Missing income evidence.",
            missing_items=("pay_stub", "bank_statement"),
        )
        los_adapter.notify_readiness("LOS-REF-001", status)  # must not raise

    def test_notify_returns_none(self, los_adapter: LOSAdapter) -> None:
        status = ReadinessStatus(
            los_reference="LOS-REF-001",
            is_ready=True,
            summary="Ready.",
        )
        result = los_adapter.notify_readiness("LOS-REF-001", status)
        assert result is None


class TestDataTypeValidation:
    """Constructor validation on LOS data types."""

    def test_application_data_empty_reference_raises(self) -> None:
        with pytest.raises(ValueError, match="los_reference"):
            ApplicationData(los_reference="", application_type="purchase", metadata={})

    def test_document_reference_empty_reference_raises(self) -> None:
        with pytest.raises(ValueError, match="los_reference"):
            DocumentReference(
                los_reference="",
                document_name="Pay Stub",
                document_type="pay_stub",
            )

    def test_document_reference_empty_type_raises(self) -> None:
        with pytest.raises(ValueError, match="document_type"):
            DocumentReference(
                los_reference="LOS-DOC-001",
                document_name="Pay Stub",
                document_type="",
            )

    def test_readiness_status_empty_reference_raises(self) -> None:
        with pytest.raises(ValueError, match="los_reference"):
            ReadinessStatus(
                los_reference="",
                is_ready=True,
                summary="Ready.",
            )

    def test_readiness_status_missing_items_defaults_empty(self) -> None:
        status = ReadinessStatus(
            los_reference="LOS-001",
            is_ready=True,
            summary="Ready.",
        )
        assert status.missing_items == ()
