"""
Pydantic request and response DTOs for the MIL Platform REST API (v1).

All schemas use Pydantic v2.  Route handlers must not return domain model
objects directly — they must convert to a response schema before returning.

Schema → domain model coupling:
  The ``from_model`` classmethods accept the corresponding domain ORM objects
  (imported under ``TYPE_CHECKING`` to prevent runtime circular imports).
  The field mapping is explicit — no ``from_attributes`` magic — so that
  schema changes are always deliberate.

Dependency rule: imports domain model types under ``TYPE_CHECKING`` only.
No bounded context import appears at runtime.  Pydantic and standard library
only at runtime.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from mil.application.models import MortgageApplication, Party
    from mil.document.models import Document

# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Canonical error response body — mirrors ``APIErrorResponse``."""

    code: str
    message: str
    details: list[object] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Application schemas
# ---------------------------------------------------------------------------


class CreateApplicationRequest(BaseModel):
    """Request body for POST /v1/applications."""

    los_reference: str | None = Field(
        default=None,
        description="External LOS application identifier; may be provided later.",
        max_length=255,
    )


class ApplicationResponse(BaseModel):
    """Application resource representation."""

    id: UUID
    los_reference: str | None = None
    status: str
    active_policy_pack_id: UUID | None = None
    party_count: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=False)

    @classmethod
    def from_model(cls, app: MortgageApplication) -> ApplicationResponse:
        parties: list[object] = list(app.parties) if app.parties is not None else []
        return cls(
            id=app.id,
            los_reference=app.los_reference,
            status=app.status,
            active_policy_pack_id=app.active_policy_pack_id,
            party_count=len(parties),
            created_at=app.created_at,
            updated_at=app.updated_at,
        )


class ApplicationListResponse(BaseModel):
    """Paginated application list."""

    items: list[ApplicationResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Party schemas
# ---------------------------------------------------------------------------


class AddPartyRequest(BaseModel):
    """Request body for POST /v1/applications/{id}/parties."""

    party_type: str = Field(
        description="Role the party plays: APPLICANT, CO_APPLICANT, GUARANTOR, CORPORATE_ENTITY.",
    )
    display_name: str = Field(
        description="Non-PII display label for this party (e.g. 'Primary Borrower').",
        min_length=1,
        max_length=255,
    )


class PartyResponse(BaseModel):
    """Party resource representation."""

    id: UUID
    application_id: UUID
    party_type: str
    display_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=False)

    @classmethod
    def from_model(cls, party: Party) -> PartyResponse:
        return cls(
            id=party.id,
            application_id=party.application_id,
            party_type=party.party_type,
            display_name=party.display_name,
            created_at=party.created_at,
        )


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------


class DocumentResponse(BaseModel):
    """
    Document resource representation.

    ``document_type`` maps to ``Document.mime_type``.  In Sprint 3D the form
    field ``document_type`` (a business classification such as BANK_STATEMENT)
    is stored as ``mime_type`` on the domain model.  A dedicated
    ``document_type`` column will be added in a future sprint migration once
    the business classification taxonomy is finalised.

    ``evidence_item_count`` is always 0 in Sprint 3D (no evidence pipeline yet).
    ``page_count`` and ``ingestion_completed_at`` are not tracked in Sprint 3D.
    """

    id: UUID
    application_id: UUID
    party_id: UUID | None = None
    document_type: str = Field(
        description="Business document classification (e.g. BANK_STATEMENT, PAYSLIP)."
    )
    ingestion_status: str
    content_hash: str = Field(description="SHA-256 hex digest of the original file bytes.")
    uploaded_at: datetime
    uploaded_by: UUID
    evidence_item_count: int = 0
    page_count: int | None = None
    ingestion_completed_at: datetime | None = None
    ingestion_error: str | None = None

    model_config = ConfigDict(from_attributes=False)

    @classmethod
    def from_model(cls, doc: Document) -> DocumentResponse:
        return cls(
            id=doc.id,
            application_id=doc.application_id,
            party_id=doc.party_id,
            document_type=doc.mime_type,
            ingestion_status=doc.ingestion_status,
            content_hash=doc.content_hash,
            uploaded_at=doc.uploaded_at,
            uploaded_by=doc.uploaded_by,
        )


# ---------------------------------------------------------------------------
# Auth / System schemas
# ---------------------------------------------------------------------------


class CurrentUserResponse(BaseModel):
    """Response for GET /v1/me — the authenticated caller's identity."""

    user_id: UUID
    tenant_id: UUID
    roles: list[str]
    email: str
    display_name: str


class HealthResponse(BaseModel):
    """Response for GET /v1/health."""

    status: str = "ok"
    version: str = "1.0.0"
    environment: str = "development"
