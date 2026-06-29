"""
MockLOSAdapter — development LOS adapter.

Returns deterministic ``ApplicationData`` and ``DocumentReference`` objects
for any LOS reference.  Intended for local development, unit tests, and
conformance test verification.

MUST NOT be registered in staging or production containers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mil.kernel.providers.los_adapter import (
    ApplicationData,
    DocumentReference,
    LOSAdapter,
)

if TYPE_CHECKING:
    from mil.kernel.providers.los_adapter import ReadinessStatus

_DEFAULT_APP_TYPE = "purchase"


class MockLOSAdapter(LOSAdapter):
    """
    Deterministic LOS adapter for development and testing.

    Returns hard-coded application data and document references for any
    LOS reference string.  Readiness notifications are accepted and silently
    discarded (stored in ``_notifications`` for test assertions).

    Configurable application data:

    Pass a ``known_applications`` dict to provide per-reference application
    data.  Any reference not in the dict falls back to a default mock::

        adapter = MockLOSAdapter(known_applications={
            "LOS-001": ApplicationData(
                los_reference="LOS-001",
                application_type="purchase",
                metadata={"applicant_name": "Jane Test"},
            )
        })
    """

    def __init__(
        self,
        known_applications: dict[str, ApplicationData] | None = None,
        known_documents: dict[str, list[DocumentReference]] | None = None,
    ) -> None:
        self._known_applications: dict[str, ApplicationData] = known_applications or {}
        self._known_documents: dict[str, list[DocumentReference]] = known_documents or {}
        self._notifications: list[tuple[str, ReadinessStatus]] = []

    def read_application(self, los_reference: str) -> ApplicationData:
        if los_reference in self._known_applications:
            return self._known_applications[los_reference]

        return ApplicationData(
            los_reference=los_reference,
            application_type=_DEFAULT_APP_TYPE,
            metadata={
                "applicant_name": "Mock Applicant",
                "loan_amount": "250000",
                "property_address": "1 Mock Street, Test City",
                "application_date": "2026-01-15",
            },
        )

    def read_documents(self, los_reference: str) -> list[DocumentReference]:
        if los_reference in self._known_documents:
            return list(self._known_documents[los_reference])

        return [
            DocumentReference(
                los_reference=f"{los_reference}-DOC-001",
                document_name="Pay Stub - January 2026",
                document_type="pay_stub",
                content_url=None,
            ),
            DocumentReference(
                los_reference=f"{los_reference}-DOC-002",
                document_name="Bank Statement - Q4 2025",
                document_type="bank_statement",
                content_url=None,
            ),
        ]

    def notify_readiness(self, los_reference: str, status: ReadinessStatus) -> None:
        self._notifications.append((los_reference, status))

    @property
    def notifications(self) -> list[tuple[str, ReadinessStatus]]:
        """List of (los_reference, ReadinessStatus) tuples received via ``notify_readiness``."""
        return list(self._notifications)
