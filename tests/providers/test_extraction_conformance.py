"""
ExtractionProvider conformance tests.

Verifies that any concrete ``ExtractionProvider`` satisfies the interface
contract defined in ``mil.kernel.providers.extraction``, including the
mandatory presence of all seven provenance attributes on every returned
``EvidenceAttributes`` object.

Engineering Constitution Principle II (Evidence First): no ``EvidenceAttributes``
object is considered valid unless all seven provenance attributes are
populated to the extent derivable from the source.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from mil.kernel.providers.extraction import (
    EvidenceAttributes,
    ExtractionProvider,
    FieldLocation,
)

if TYPE_CHECKING:
    from mil.kernel.providers.ocr import OCRProvider, OCRResult


@pytest.fixture
def ocr_result(ocr_provider: OCRProvider, sample_pdf_bytes: bytes) -> OCRResult:
    return ocr_provider.process_document("doc-ref-001", sample_pdf_bytes)


class TestExtractionProviderInterfaceContract:
    """Verify the abstract interface structure."""

    def test_extraction_provider_is_abstract(self) -> None:
        assert ExtractionProvider.__abstractmethods__ != set()

    def test_extract_evidence_is_abstract(self) -> None:
        assert "extract_evidence" in ExtractionProvider.__abstractmethods__

    def test_version_is_abstract(self) -> None:
        assert "version" in ExtractionProvider.__abstractmethods__

    def test_concrete_provider_is_subclass(self, extraction_provider: ExtractionProvider) -> None:
        assert isinstance(extraction_provider, ExtractionProvider)


class TestExtractionProviderVersion:
    """Version contract: providers MUST return a non-empty version string."""

    def test_version_returns_string(self, extraction_provider: ExtractionProvider) -> None:
        assert isinstance(extraction_provider.version(), str)

    def test_version_is_non_empty(self, extraction_provider: ExtractionProvider) -> None:
        assert extraction_provider.version() != ""


class TestExtractEvidenceReturnType:
    """extract_evidence must return a list (never None)."""

    def test_returns_list(
        self,
        extraction_provider: ExtractionProvider,
        ocr_result: OCRResult,
    ) -> None:
        result = extraction_provider.extract_evidence(ocr_result, "doc-id-001")
        assert isinstance(result, list)

    def test_returns_at_least_one_item(
        self,
        extraction_provider: ExtractionProvider,
        ocr_result: OCRResult,
    ) -> None:
        result = extraction_provider.extract_evidence(ocr_result, "doc-id-001")
        assert len(result) >= 1

    def test_all_items_are_evidence_attributes(
        self,
        extraction_provider: ExtractionProvider,
        ocr_result: OCRResult,
    ) -> None:
        result = extraction_provider.extract_evidence(ocr_result, "doc-id-001")
        for item in result:
            assert isinstance(item, EvidenceAttributes)


class TestEvidenceProvenanceAttributes:
    """
    All seven provenance attributes must be present and non-empty on every
    returned EvidenceAttributes object (Principle II compliance).
    """

    @pytest.fixture
    def evidence_items(
        self,
        extraction_provider: ExtractionProvider,
        ocr_result: OCRResult,
    ) -> list[EvidenceAttributes]:
        return extraction_provider.extract_evidence(ocr_result, "doc-id-001")

    # Provenance attribute 1: source document
    def test_source_document_ref_is_non_empty(
        self, evidence_items: list[EvidenceAttributes]
    ) -> None:
        for item in evidence_items:
            assert item.source_document_ref != "", (
                f"source_document_ref is empty for field {item.field_name!r}"
            )

    # Provenance attribute 2: page number
    def test_page_number_is_positive(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert item.page_number >= 1, f"page_number < 1 for field {item.field_name!r}"

    # Provenance attribute 3: field location (may be None for plain text)
    def test_field_location_is_field_location_or_none(
        self, evidence_items: list[EvidenceAttributes]
    ) -> None:
        for item in evidence_items:
            assert item.field_location is None or isinstance(item.field_location, FieldLocation)

    # Provenance attribute 4: extraction confidence in [0.0, 1.0]
    def test_extraction_confidence_in_range(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert 0.0 <= item.extraction_confidence <= 1.0, (
                f"extraction_confidence {item.extraction_confidence!r} out of range "
                f"for field {item.field_name!r}"
            )

    # Provenance attribute 5: extraction method
    def test_extraction_method_is_non_empty(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert item.extraction_method != "", (
                f"extraction_method is empty for field {item.field_name!r}"
            )

    # Provenance attribute 6: timestamp
    def test_extracted_at_is_aware_datetime(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert isinstance(item.extracted_at, datetime), (
                f"extracted_at is not a datetime for field {item.field_name!r}"
            )
            assert item.extracted_at.tzinfo is not None, (
                f"extracted_at is naive (no timezone) for field {item.field_name!r}"
            )

    # Provenance attribute 7: extraction version (originating model version)
    def test_extraction_version_is_non_empty(
        self, evidence_items: list[EvidenceAttributes]
    ) -> None:
        for item in evidence_items:
            assert item.extraction_version != "", (
                f"extraction_version is empty for field {item.field_name!r}"
            )

    def test_extraction_version_matches_provider_version(
        self,
        extraction_provider: ExtractionProvider,
        evidence_items: list[EvidenceAttributes],
    ) -> None:
        for item in evidence_items:
            assert item.extraction_version == extraction_provider.version()


class TestEvidenceAttributesFields:
    """Core domain fields must be present on every item."""

    @pytest.fixture
    def evidence_items(
        self,
        extraction_provider: ExtractionProvider,
        ocr_result: OCRResult,
    ) -> list[EvidenceAttributes]:
        return extraction_provider.extract_evidence(ocr_result, "doc-id-001")

    def test_field_name_is_non_empty(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert item.field_name != ""

    def test_document_id_echoed(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert item.document_id == "doc-id-001"

    def test_provenance_complete_method(self, evidence_items: list[EvidenceAttributes]) -> None:
        for item in evidence_items:
            assert item.provenance_complete(), (
                f"provenance_complete() returned False for {item.field_name!r}"
            )


class TestEvidenceAttributesValidation:
    """EvidenceAttributes constructor validates its own constraints."""

    def test_empty_field_name_raises(self) -> None:
        from mil.kernel.providers.extraction import make_evidence_attributes

        with pytest.raises(ValueError, match="field_name"):
            make_evidence_attributes(
                field_name="",
                field_value="value",
                document_id="doc-1",
                source_document_ref="s3://bucket/doc",
                page_number=1,
                field_location=None,
                extraction_confidence=0.9,
                extraction_method="test-method",
                extraction_version="1.0.0",
            )

    def test_confidence_out_of_range_raises(self) -> None:
        from mil.kernel.providers.extraction import make_evidence_attributes

        with pytest.raises(ValueError, match="extraction_confidence"):
            make_evidence_attributes(
                field_name="income",
                field_value="5000",
                document_id="doc-1",
                source_document_ref="s3://bucket/doc",
                page_number=1,
                field_location=None,
                extraction_confidence=1.5,
                extraction_method="test-method",
                extraction_version="1.0.0",
            )

    def test_invalid_page_number_raises(self) -> None:
        from mil.kernel.providers.extraction import make_evidence_attributes

        with pytest.raises(ValueError, match="page_number"):
            make_evidence_attributes(
                field_name="income",
                field_value="5000",
                document_id="doc-1",
                source_document_ref="s3://bucket/doc",
                page_number=0,
                field_location=None,
                extraction_confidence=0.9,
                extraction_method="test-method",
                extraction_version="1.0.0",
            )
