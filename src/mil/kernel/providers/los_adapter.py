"""
LOSAdapter interface for the MIL Platform.

Translates between MIL's domain model and a specific Loan Origination System (LOS)
data format.  Each LOS platform requires a separate concrete implementation;
the core MIL platform contains no LOS-specific code.

This module defines only the abstract interface and its data types.
Concrete implementations live in ``src/providers/los/`` and are registered
via ``ProviderRegistry.register_los_adapter()``.

Engineering Constitution Principle VI (API-First Integration): MIL must remain
vendor-agnostic.  The ``LOSAdapter`` is the sole boundary between MIL's domain
model and any external LOS data format.  LOS-specific field names, date formats,
identifier schemes, and status codes are translated inside the adapter
implementation — never in the MIL domain.

Dependency rule: this module imports from the Python standard library only.
No bounded context code should be imported here.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# LOS adapter data types
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ApplicationData:
    """
    MIL-normalised representation of a mortgage application read from a LOS.

    The ``metadata`` dict carries LOS-specific fields that have been translated
    to generic, string-typed key-value pairs.  The bounded context consuming
    this data is responsible for type-casting specific fields.

    This class is NOT frozen because the ``metadata`` dict is mutable.
    Callers should treat instances as read-only; downstream code MUST NOT
    modify fields after construction.

    Attributes:
        los_reference:    The original LOS identifier for this application.
        application_type: Normalised application type string (e.g.
                          ``"purchase"``, ``"refinance"``).
        metadata:         LOS-specific fields translated to generic form.
                          Keys use snake_case MIL naming conventions.
    """

    los_reference: str
    application_type: str
    metadata: dict[str, str]

    def __post_init__(self) -> None:
        if not self.los_reference:
            raise ValueError("los_reference cannot be empty")


@dataclasses.dataclass
class DocumentReference:
    """
    A reference to a document held in a LOS.

    Adapters return a list of these from ``read_documents()`` so that the
    MIL Document service can ingest each document individually without
    coupling to any LOS-specific retrieval mechanism.

    Attributes:
        los_reference:  The LOS identifier for this document.
        document_name:  Human-readable document name (e.g. ``"Pay Stub - Jan 2026"``).
        document_type:  Normalised MIL document type string.
        content_url:    A URL or URI from which the document bytes can be
                        fetched.  ``None`` for document types that are
                        available only via LOS-proprietary APIs.
    """

    los_reference: str
    document_name: str
    document_type: str
    content_url: str | None = None

    def __post_init__(self) -> None:
        if not self.los_reference:
            raise ValueError("los_reference cannot be empty")
        if not self.document_type:
            raise ValueError("document_type cannot be empty")


@dataclasses.dataclass(frozen=True)
class ReadinessStatus:
    """
    Mortgage Readiness assessment to be dispatched back to the LOS.

    Carries MIL's readiness evaluation result in a format that the
    ``LOSAdapter`` translates into LOS-specific status fields.

    MIL MUST NOT write directly to the LOS.  The adapter translates this
    object into a notification call on the LOS API — read → enrich → return.

    Attributes:
        los_reference: The LOS application identifier.
        is_ready:      ``True`` if the application is ready for underwriting.
        summary:       Human-readable summary of the readiness assessment.
        missing_items: Tuple of items preventing readiness (empty when ready).
    """

    los_reference: str
    is_ready: bool
    summary: str
    missing_items: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.los_reference:
            raise ValueError("los_reference cannot be empty")


# ---------------------------------------------------------------------------
# Abstract LOSAdapter interface
# ---------------------------------------------------------------------------


class LOSAdapter(ABC):
    """
    Abstract interface for LOS integration.

    Each LOS platform that MIL integrates with requires a concrete
    implementation of this interface.  The implementation encapsulates all
    LOS-specific knowledge: field name translation, authentication, date
    format normalisation, and identifier mapping.

    The core MIL platform resolves ``LOSAdapter`` from the DI container.
    It has no dependency on any specific adapter implementation.

    Engineering Constitution Principle VI: MIL MUST NOT perform autonomous
    write operations into an LOS.  ``notify_readiness`` is the only write
    method, and it merely proposes a status notification — the LOS receives
    a readiness signal and decides how to act on it.
    """

    @abstractmethod
    def read_application(self, los_reference: str) -> ApplicationData:
        """
        Read and normalise application data from the LOS.

        Args:
            los_reference: The LOS-specific application identifier.

        Returns:
            ``ApplicationData`` with normalised fields.

        Raises:
            ProviderError: If the LOS is unavailable or the reference is invalid.
        """

    @abstractmethod
    def read_documents(self, los_reference: str) -> list[DocumentReference]:
        """
        Return references to all documents associated with a LOS application.

        Args:
            los_reference: The LOS-specific application identifier.

        Returns:
            List of ``DocumentReference`` objects.  Returns an empty list
            if no documents are associated; never returns ``None``.

        Raises:
            ProviderError: If the LOS is unavailable.
        """

    @abstractmethod
    def notify_readiness(self, los_reference: str, status: ReadinessStatus) -> None:
        """
        Send a Mortgage Readiness status notification to the LOS.

        This is the only write-direction operation in the LOSAdapter interface.
        The LOS receives a readiness signal; any resulting state change within
        the LOS is initiated by the LOS itself, not by MIL.

        Args:
            los_reference: The LOS-specific application identifier.
            status:        The readiness assessment to communicate.

        Raises:
            ProviderError: If the notification cannot be delivered.
        """
