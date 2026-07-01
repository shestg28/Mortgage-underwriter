"""Unit tests for mil.document.ocr_models — OCRResultRecord."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from mil.document.ocr_models import OCRResultRecord
from mil.kernel.providers.ocr import OCRResult, PageLayout, PageText

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ocr_result(version: str = "mock-ocr-1.0.0") -> OCRResult:
    page1 = PageText(
        page_number=1,
        text="PAYSLIP\nGross: 5000.00",
        layout=PageLayout(page_number=1, width_points=595.0, height_points=842.0),
        word_count=3,
    )
    page2 = PageText(
        page_number=2,
        text="Tax: 1200.00",
        layout=PageLayout(page_number=2, width_points=595.0, height_points=842.0),
        word_count=2,
    )
    return OCRResult(
        document_ref="ref-1",
        pages=(page1, page2),
        provider_version=version,
        processed_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
    )


def _make_record(version: str = "mock-ocr-1.0.0") -> OCRResultRecord:
    return OCRResultRecord.create(
        document_id=uuid4(),
        workflow_run_id=uuid4(),
        tenant_id=uuid4(),
        ocr_result=_ocr_result(version),
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestCreate:
    def test_records_provider_version(self) -> None:
        record = _make_record(version="azure-di-2.1")
        assert record.provider_version == "azure-di-2.1"

    def test_records_page_count(self) -> None:
        assert _make_record().page_count == 2

    def test_records_full_text(self) -> None:
        record = _make_record()
        assert "PAYSLIP" in record.full_text
        assert "Tax: 1200.00" in record.full_text

    def test_serialises_pages_with_layout(self) -> None:
        record = _make_record()
        assert len(record.pages) == 2
        first = record.pages[0]
        assert first["page_number"] == 1
        assert first["width_points"] == 595.0
        assert first["height_points"] == 842.0
        assert first["word_count"] == 3

    def test_records_processed_at_from_provider(self) -> None:
        record = _make_record()
        assert record.processed_at == datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    def test_sets_created_at(self) -> None:
        assert _make_record().created_at is not None

    def test_links_document_and_run_and_tenant(self) -> None:
        record = _make_record()
        assert record.document_id is not None
        assert record.workflow_run_id is not None
        assert record.tenant_id is not None


# ---------------------------------------------------------------------------
# Determinism: same document + provider version → same content
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_inputs_produce_same_text_and_count(self) -> None:
        doc_id = uuid4()
        run_id = uuid4()
        tenant_id = uuid4()
        r1 = OCRResultRecord.create(
            document_id=doc_id,
            workflow_run_id=run_id,
            tenant_id=tenant_id,
            ocr_result=_ocr_result("v1"),
        )
        r2 = OCRResultRecord.create(
            document_id=doc_id,
            workflow_run_id=run_id,
            tenant_id=tenant_id,
            ocr_result=_ocr_result("v1"),
        )
        assert r1.full_text == r2.full_text
        assert r1.page_count == r2.page_count
        assert r1.provider_version == r2.provider_version


# ---------------------------------------------------------------------------
# Reconstruction for the Extraction stage
# ---------------------------------------------------------------------------


class TestToOcrResult:
    def test_roundtrip_preserves_provider_version(self) -> None:
        record = _make_record(version="v9")
        assert record.to_ocr_result().provider_version == "v9"

    def test_roundtrip_preserves_page_count(self) -> None:
        record = _make_record()
        assert record.to_ocr_result().page_count == 2

    def test_roundtrip_preserves_text(self) -> None:
        record = _make_record()
        reconstructed = record.to_ocr_result()
        assert reconstructed.pages[0].text == "PAYSLIP\nGross: 5000.00"

    def test_roundtrip_preserves_layout(self) -> None:
        record = _make_record()
        layout = record.to_ocr_result().pages[0].layout
        assert layout.width_points == 595.0
        assert layout.height_points == 842.0


# ---------------------------------------------------------------------------
# ORM metadata
# ---------------------------------------------------------------------------


class TestOrmMetadata:
    def test_table_in_core_schema(self) -> None:
        assert OCRResultRecord.__table__.schema == "core"

    def test_unique_constraint_on_document_and_version(self) -> None:
        names = {c.name for c in OCRResultRecord.__table__.constraints}
        assert "uq_document_ocr_results_document_version" in names
