"""
ORM model for persisted OCR output (Document Processing bounded context).

``OCRResultRecord`` is the durable, immutable record of the text and layout an
OCR engine produced for a document. It is stored separately from ``Document``
(which remains the custody record, ADR-006) and is never overwritten.

Determinism (Principle XII): the same document processed by the same OCR
provider version always yields the same stored result. ``(document_id,
provider_version)`` is unique — a re-run under an identical provider version
finds the existing row rather than creating a duplicate, and the platform can
always answer "which OCR engine produced this text?" from ``provider_version``.

The structured per-page layout is preserved in ``pages`` (JSON) so the
Extraction stage (a later sprint) can consume positional metadata. ``full_text``
holds the concatenated plain text for convenience.

Schema: ``core`` PostgreSQL schema (alongside ``core.documents``).

Dependency rule: imports only from ``mil.kernel`` and the Python standard
library.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mil.kernel.db import Base

if TYPE_CHECKING:
    from mil.kernel.providers.ocr import OCRResult


def _serialise_pages(result: OCRResult) -> list[dict[str, object]]:
    """Serialise the per-page text and layout into JSON-safe dicts."""
    return [
        {
            "page_number": page.page_number,
            "text": page.text,
            "word_count": page.word_count,
            "width_points": page.layout.width_points,
            "height_points": page.layout.height_points,
        }
        for page in result.pages
    ]


class OCRResultRecord(Base):
    """
    Immutable persisted OCR output for a single document.

    Created once by the OCR worker and never updated. References the source
    document (custody record) and the workflow run that produced it (lineage),
    and records the provider version for attribution and determinism.
    """

    __tablename__ = "document_ocr_results"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "provider_version", name="uq_document_ocr_results_document_version"
        ),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("core.documents.id"), nullable=False)
    workflow_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("orchestrator.workflow_runs.id"), nullable=False
    )
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    # Which OCR engine produced this text — the determinism / attribution anchor.
    provider_version: Mapped[str] = mapped_column(String(100), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # Concatenated plain text across pages (convenience for extraction).
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Structured per-page text + layout, preserving positional metadata.
    pages: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        document_id: UUID,
        workflow_run_id: UUID,
        tenant_id: UUID,
        ocr_result: OCRResult,
    ) -> OCRResultRecord:
        """
        Build an immutable record from a provider ``OCRResult``.

        Captures the provider version, page count, full text, structured page
        layout, and the provider's ``processed_at`` timestamp. The record is
        returned unattached to a session — the repository persists it.
        """
        return cls(
            id=uuid4(),
            document_id=document_id,
            workflow_run_id=workflow_run_id,
            tenant_id=tenant_id,
            provider_version=ocr_result.provider_version,
            page_count=ocr_result.page_count,
            full_text=ocr_result.full_text,
            pages=_serialise_pages(ocr_result),
            processed_at=ocr_result.processed_at,
            created_at=datetime.now(UTC),
        )

    # ------------------------------------------------------------------
    # Reconstruction (input to the Extraction stage, a later sprint)
    # ------------------------------------------------------------------

    def to_ocr_result(self) -> OCRResult:
        """
        Reconstruct the provider ``OCRResult`` dataclass from stored fields.

        Lets the Extraction stage consume persisted OCR output through the same
        typed contract the OCR provider produced, without re-running OCR.
        """
        from mil.kernel.providers.ocr import OCRResult, PageLayout, PageText

        pages = tuple(
            PageText(
                page_number=int(str(p["page_number"])),
                text=str(p["text"]),
                layout=PageLayout(
                    page_number=int(str(p["page_number"])),
                    width_points=float(str(p["width_points"])),
                    height_points=float(str(p["height_points"])),
                ),
                word_count=int(str(p.get("word_count", 0))),
            )
            for p in self.pages
        )
        return OCRResult(
            document_ref=str(self.document_id),
            pages=pages,
            provider_version=self.provider_version,
            processed_at=self.processed_at,
        )

    def __repr__(self) -> str:
        return (
            f"<OCRResultRecord id={self.id} document={self.document_id} "
            f"provider={self.provider_version} pages={self.page_count}>"
        )
