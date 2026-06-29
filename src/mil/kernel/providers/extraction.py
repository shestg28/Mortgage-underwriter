"""
ExtractionProvider interface for the MIL Platform.

Extracts typed Evidence attributes from OCR output.  Every ``EvidenceAttributes``
object returned by this provider MUST carry all seven provenance attributes
mandated by Engineering Constitution Principle II (Evidence First).

This module defines only the abstract interface and its data types.
Concrete implementations live in ``src/providers/extraction/`` and are
registered via ``ProviderRegistry.register_extraction()``.

Dependency rule: this module imports from ``mil.kernel.providers.ocr`` and
the Python standard library only.  No bounded context code should be imported.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mil.kernel.providers.ocr import OCRResult


# ---------------------------------------------------------------------------
# Extraction data types
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FieldLocation:
    """
    Position of a specific field within a document page.

    ``bounding_box`` is an optional (x, y, width, height) tuple expressed
    as fractions of page dimensions in the range [0.0, 1.0].  ``None`` when
    the provider cannot determine a precise location.
    """

    page_number: int
    field_name: str
    bounding_box: tuple[float, float, float, float] | None = None


@dataclasses.dataclass(frozen=True)
class EvidenceAttributes:
    """
    Structured Evidence attributes extracted from a document.

    All seven provenance attributes mandated by Engineering Constitution
    Principle II (Evidence First) are required fields:

    ==============================  =============================================
    Attribute                       Mapped field
    ==============================  =============================================
    Source document                 ``source_document_ref``
    Page number                     ``page_number``
    Field location                  ``field_location``  (``None`` when unknown)
    Extraction confidence           ``extraction_confidence``  [0.0, 1.0]
    Extraction method               ``extraction_method``
    Timestamp                       ``extracted_at``
    Originating model version       ``extraction_version``
    ==============================  =============================================

    The ``ExtractionProvider.extract_evidence`` method MUST raise
    ``ProviderError`` rather than returning an ``EvidenceAttributes`` object
    with any of these fields unset / empty.

    Additional fields:
        - ``field_name`` — machine-readable identifier for the extracted fact
          (e.g. ``"monthly_income"``).
        - ``field_value`` — the extracted value as a string.  Callers are
          responsible for type-casting after validation.
        - ``document_id`` — the MIL document identifier for the source document
          (separate from the storage reference so both are traceable).
    """

    # Required domain fields
    field_name: str
    field_value: str
    document_id: str

    # Provenance attribute 1: source document
    source_document_ref: str

    # Provenance attribute 2: page number
    page_number: int

    # Provenance attribute 3: field location (None when not determinable)
    field_location: FieldLocation | None

    # Provenance attribute 4: extraction confidence
    extraction_confidence: float

    # Provenance attribute 5: extraction method
    extraction_method: str

    # Provenance attribute 6: timestamp
    extracted_at: datetime

    # Provenance attribute 7: originating model / engine version
    extraction_version: str

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name cannot be empty")
        if not self.source_document_ref:
            raise ValueError("source_document_ref cannot be empty")
        if not self.extraction_method:
            raise ValueError("extraction_method cannot be empty")
        if not self.extraction_version:
            raise ValueError("extraction_version cannot be empty")
        if not (0.0 <= self.extraction_confidence <= 1.0):
            raise ValueError(
                f"extraction_confidence must be in [0.0, 1.0], got {self.extraction_confidence}"
            )
        if self.page_number < 1:
            raise ValueError(f"page_number must be >= 1, got {self.page_number}")
        if self.extracted_at.tzinfo is None:
            raise ValueError("extracted_at must be timezone-aware")

    @property
    def has_field_location(self) -> bool:
        """Return ``True`` if a precise field location was determined."""
        return self.field_location is not None

    def provenance_complete(self) -> bool:
        """
        Return ``True`` if all seven provenance attributes are populated to
        the extent they are derivable from the source.

        The ``field_location`` attribute may be ``None`` for sources that do
        not provide positional metadata (e.g. plain-text documents).
        """
        return bool(
            self.source_document_ref
            and self.page_number >= 1
            and self.extraction_method
            and self.extraction_version
            and self.extracted_at.tzinfo is not None
        )


# ---------------------------------------------------------------------------
# Abstract ExtractionProvider interface
# ---------------------------------------------------------------------------


class ExtractionProvider(ABC):
    """
    Abstract interface for evidence attribute extraction from OCR output.

    Takes structured OCR output produced by an ``OCRProvider`` and returns
    a list of typed evidence attributes, each carrying all seven provenance
    fields required by Principle II.

    The extraction engine is independent of the upstream OCR engine: any
    ``OCRResult`` produced by any ``OCRProvider`` implementation can be
    passed to any ``ExtractionProvider`` implementation.

    Version contract: every ``EvidenceAttributes`` object MUST include a
    non-empty ``extraction_version`` string.  This string is recorded on the
    ``EvidenceItem`` domain entity and retained in the audit record.
    """

    @abstractmethod
    def extract_evidence(
        self,
        ocr_result: OCRResult,
        document_id: str,
    ) -> list[EvidenceAttributes]:
        """
        Extract Evidence attributes from OCR output for a given document.

        Args:
            ocr_result:  The structured OCR output produced by an ``OCRProvider``.
            document_id: The MIL document identifier for traceability.

        Returns:
            A list of ``EvidenceAttributes`` objects, each carrying all seven
            provenance attributes.  Returns an empty list if no evidence is
            found; never returns ``None``.

        Raises:
            ProviderError: If extraction fails or returns incomplete provenance.
        """

    @abstractmethod
    def version(self) -> str:
        """
        Return the version identifier for this extraction provider implementation.

        This is the same string included in every ``EvidenceAttributes.extraction_version``.
        Used by ``ProviderRegistry`` to validate provider registration.
        """


# ---------------------------------------------------------------------------
# Helper to build an EvidenceAttributes with current UTC timestamp
# ---------------------------------------------------------------------------


def make_evidence_attributes(
    *,
    field_name: str,
    field_value: str,
    document_id: str,
    source_document_ref: str,
    page_number: int,
    field_location: FieldLocation | None,
    extraction_confidence: float,
    extraction_method: str,
    extraction_version: str,
    extracted_at: datetime | None = None,
) -> EvidenceAttributes:
    """
    Construct an ``EvidenceAttributes`` with all seven provenance fields.

    The ``extracted_at`` argument defaults to the current UTC time when
    omitted, which is the expected usage for live extraction.  Pass an
    explicit value in tests or when replaying historical extractions.
    """
    ts = extracted_at if extracted_at is not None else datetime.now(UTC)
    return EvidenceAttributes(
        field_name=field_name,
        field_value=field_value,
        document_id=document_id,
        source_document_ref=source_document_ref,
        page_number=page_number,
        field_location=field_location,
        extraction_confidence=extraction_confidence,
        extraction_method=extraction_method,
        extracted_at=ts,
        extraction_version=extraction_version,
    )
