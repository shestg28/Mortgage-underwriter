"""
Persistence gateway for OCR results (Document Processing bounded context).

``OCRResultRepository`` is append-only: it writes immutable ``OCRResultRecord``
rows and never updates or deletes them (ADR-006 immutability discipline applied
to derived OCR output). It does not commit — the caller (the OCR worker's
per-job Unit of Work) owns the transaction.

Idempotency (ADR-008): ``get_by_document_and_version`` lets the worker detect a
replay (an OCR result already exists for this document and provider version) and
treat it as a no-op rather than creating a duplicate; the unique constraint on
``(document_id, provider_version)`` is the backing authority.

Dependency rule: imports only from ``mil.document.ocr_models``, ``mil.kernel``,
and the Python standard library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from mil.document.ocr_models import OCRResultRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class OCRResultRepository:
    """Append-only gateway for ``OCRResultRecord`` rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, record: OCRResultRecord) -> None:
        """
        Persist an immutable OCR result.

        Adds the record and flushes so a uniqueness violation (duplicate
        document+version) surfaces within the caller's transaction.
        """
        self._session.add(record)
        self._session.flush()

    def get_by_document_and_version(
        self, document_id: UUID, provider_version: str
    ) -> OCRResultRecord | None:
        """
        Return the OCR result for a document under a provider version, or ``None``.

        This is the idempotency lookup: a non-``None`` result means OCR has
        already been completed deterministically for this (document, version).
        """
        stmt = select(OCRResultRecord).where(
            OCRResultRecord.document_id == document_id,
            OCRResultRecord.provider_version == provider_version,
        )
        return self._session.scalars(stmt).one_or_none()

    def get_for_document(self, document_id: UUID) -> list[OCRResultRecord]:
        """Return all OCR results for a document, most recent first."""
        stmt = (
            select(OCRResultRecord)
            .where(OCRResultRecord.document_id == document_id)
            .order_by(OCRResultRecord.created_at.desc())
        )
        return list(self._session.scalars(stmt))

    def exists_for_document_and_version(self, document_id: UUID, provider_version: str) -> bool:
        """Return ``True`` if an OCR result already exists for (document, version)."""
        return self.get_by_document_and_version(document_id, provider_version) is not None
