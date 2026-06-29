"""
OCRProvider interface for the MIL Platform.

Converts scanned and image-based documents into machine-readable text
with structured page layout metadata.  Every result carries the provider's
version identifier so it can be recorded on Evidence items per
Engineering Constitution Principle XII (Deterministic Intelligence).

This module defines only the abstract interface and the data types it
operates on.  Concrete implementations live in ``src/providers/ocr/``
and are registered in the DI container at startup.

Dependency rule: this module imports only from the Python standard library.
No bounded context code should be imported here.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# OCR data types
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class PageLayout:
    """
    Physical dimensions and positional metadata for a single document page.

    All measurements are in PDF points (1 point = 1/72 inch).
    """

    page_number: int
    width_points: float
    height_points: float


@dataclasses.dataclass(frozen=True)
class PageText:
    """
    OCR output for a single document page.

    ``text`` is the full plain-text content extracted from the page.
    ``layout`` carries the physical dimensions for downstream coordinate
    normalisation.  ``word_count`` is a convenience counter pre-computed
    by the provider so callers do not need to tokenise.
    """

    page_number: int
    text: str
    layout: PageLayout
    word_count: int = 0


@dataclasses.dataclass(frozen=True)
class OCRResult:
    """
    Complete OCR result for a processed document.

    Attributes:
        document_ref:     The storage reference of the source document
                          (passed through from the call for audit linkage).
        pages:            Ordered tuple of per-page OCR output.
        provider_version: Version string identifying the OCR engine used.
                          Required for Principle XII attribution.
        processed_at:     UTC timestamp when OCR completed.
    """

    document_ref: str
    pages: tuple[PageText, ...]
    provider_version: str
    processed_at: datetime = dataclasses.field(
        default_factory=lambda: datetime.now(UTC),
    )

    @property
    def full_text(self) -> str:
        """Concatenated plain text from all pages, separated by double newlines."""
        return "\n\n".join(p.text for p in self.pages)

    @property
    def page_count(self) -> int:
        """Total number of pages in the OCR result."""
        return len(self.pages)


# ---------------------------------------------------------------------------
# Abstract OCRProvider interface
# ---------------------------------------------------------------------------


class OCRProvider(ABC):
    """
    Abstract interface for document OCR processing.

    Converts raw document bytes into structured page-level text.  The
    interface is independent of the underlying engine (Tesseract, Azure
    Document Intelligence, AWS Textract, Google Document AI, etc.).

    Concrete implementations are registered in the DI container at startup
    via ``ProviderRegistry.register_ocr()``.  Bounded context code resolves
    this interface from the container — it MUST NOT import concrete classes.

    Version contract: every ``OCRResult`` MUST include a non-empty
    ``provider_version`` string.  Providers that cannot determine their
    own version MUST raise ``ProviderVersionMissingError``.
    """

    @abstractmethod
    def process_document(self, document_ref: str, content: bytes) -> OCRResult:
        """
        Convert document bytes into structured page-level text.

        Args:
            document_ref: Storage reference of the document (for audit linkage).
            content:      Raw document bytes (PDF, image, etc.).

        Returns:
            ``OCRResult`` with per-page text, layout, and provider version.

        Raises:
            ProviderError:               If OCR processing fails.
            ProviderVersionMissingError: If the provider cannot report its version.
        """

    @abstractmethod
    def version(self) -> str:
        """
        Return the version identifier for this OCR provider implementation.

        This is the same string included in every ``OCRResult.provider_version``.
        Used by the ``ProviderRegistry`` to validate provider registration.
        """
