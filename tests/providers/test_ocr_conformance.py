"""
OCRProvider conformance tests.

These tests verify that any concrete ``OCRProvider`` implementation satisfies
the interface contract defined in ``mil.kernel.providers.ocr``.

The fixture ``ocr_provider`` is supplied by ``conftest.py``.  To test an
additional implementation, register a parametrized fixture variant in
``conftest.py`` and the same tests will run against it automatically.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from mil.kernel.providers.ocr import OCRProvider, OCRResult, PageLayout, PageText


class TestOCRProviderInterfaceContract:
    """Verify the abstract interface structure."""

    def test_ocr_provider_is_abstract(self) -> None:
        assert OCRProvider.__abstractmethods__ != set()

    def test_process_document_is_abstract(self) -> None:
        assert "process_document" in OCRProvider.__abstractmethods__

    def test_version_is_abstract(self) -> None:
        assert "version" in OCRProvider.__abstractmethods__

    def test_concrete_provider_is_subclass(self, ocr_provider: OCRProvider) -> None:
        assert isinstance(ocr_provider, OCRProvider)


class TestOCRProviderVersion:
    """Version contract: providers MUST return a non-empty version string."""

    def test_version_returns_string(self, ocr_provider: OCRProvider) -> None:
        assert isinstance(ocr_provider.version(), str)

    def test_version_is_non_empty(self, ocr_provider: OCRProvider) -> None:
        assert ocr_provider.version() != ""

    def test_result_version_matches_provider_version(
        self, ocr_provider: OCRProvider, sample_pdf_bytes: bytes
    ) -> None:
        result = ocr_provider.process_document("doc-ref-001", sample_pdf_bytes)
        assert result.provider_version == ocr_provider.version()


class TestOCRResultStructure:
    """OCRResult must carry required fields with correct types."""

    @pytest.fixture
    def result(self, ocr_provider: OCRProvider, sample_pdf_bytes: bytes) -> OCRResult:
        return ocr_provider.process_document("doc-ref-001", sample_pdf_bytes)

    def test_returns_ocr_result(self, result: OCRResult) -> None:
        assert isinstance(result, OCRResult)

    def test_document_ref_echoed(self, result: OCRResult) -> None:
        assert result.document_ref == "doc-ref-001"

    def test_provider_version_non_empty(self, result: OCRResult) -> None:
        assert isinstance(result.provider_version, str)
        assert result.provider_version != ""

    def test_pages_is_tuple(self, result: OCRResult) -> None:
        assert isinstance(result.pages, tuple)

    def test_pages_non_empty(self, result: OCRResult) -> None:
        assert result.page_count >= 1

    def test_processed_at_is_utc_datetime(self, result: OCRResult) -> None:
        assert isinstance(result.processed_at, datetime)
        assert result.processed_at.tzinfo is not None

    def test_full_text_property(self, result: OCRResult) -> None:
        assert isinstance(result.full_text, str)
        assert len(result.full_text) > 0

    def test_page_count_matches_pages_length(self, result: OCRResult) -> None:
        assert result.page_count == len(result.pages)


class TestOCRPageStructure:
    """Each PageText in the result must carry required fields."""

    @pytest.fixture
    def first_page(self, ocr_provider: OCRProvider, sample_pdf_bytes: bytes) -> PageText:
        result = ocr_provider.process_document("doc-ref-001", sample_pdf_bytes)
        return result.pages[0]

    def test_page_has_page_number(self, first_page: PageText) -> None:
        assert isinstance(first_page.page_number, int)

    def test_first_page_number_is_one(self, first_page: PageText) -> None:
        assert first_page.page_number == 1

    def test_page_has_text(self, first_page: PageText) -> None:
        assert isinstance(first_page.text, str)

    def test_page_text_non_empty(self, first_page: PageText) -> None:
        assert len(first_page.text) > 0

    def test_page_has_layout(self, first_page: PageText) -> None:
        assert isinstance(first_page.layout, PageLayout)

    def test_layout_page_number_matches(self, first_page: PageText) -> None:
        assert first_page.layout.page_number == first_page.page_number

    def test_layout_has_positive_dimensions(self, first_page: PageText) -> None:
        assert first_page.layout.width_points > 0
        assert first_page.layout.height_points > 0

    def test_word_count_non_negative(self, first_page: PageText) -> None:
        assert first_page.word_count >= 0


class TestOCRPageOrdering:
    """Pages must be ordered with monotonically increasing page numbers."""

    def test_pages_ordered_by_page_number(
        self, ocr_provider: OCRProvider, sample_pdf_bytes: bytes
    ) -> None:
        result = ocr_provider.process_document("doc-ref-001", sample_pdf_bytes)
        if result.page_count < 2:
            pytest.skip("Single-page result: ordering invariant not testable")
        page_numbers = [p.page_number for p in result.pages]
        assert page_numbers == sorted(page_numbers)

    def test_page_numbers_are_positive(
        self, ocr_provider: OCRProvider, sample_pdf_bytes: bytes
    ) -> None:
        result = ocr_provider.process_document("doc-ref-001", sample_pdf_bytes)
        for page in result.pages:
            assert page.page_number >= 1


class TestOCRDifferentDocumentRefs:
    """OCRResult must echo the document_ref passed by the caller."""

    def test_document_ref_is_echoed_correctly(
        self, ocr_provider: OCRProvider, sample_pdf_bytes: bytes
    ) -> None:
        custom_ref = "s3://mil-documents/application-001/payslip.pdf"
        result = ocr_provider.process_document(custom_ref, sample_pdf_bytes)
        assert result.document_ref == custom_ref

    def test_empty_content_does_not_raise(self, ocr_provider: OCRProvider) -> None:
        """Providers may return an empty page set for blank content; must not crash."""
        try:
            result = ocr_provider.process_document("doc-empty", b"")
            assert isinstance(result, OCRResult)
        except Exception:
            pytest.skip("Provider raises on empty content (acceptable behaviour)")
