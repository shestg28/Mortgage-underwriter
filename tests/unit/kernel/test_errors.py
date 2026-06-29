"""Unit tests for mil.kernel.errors — error hierarchy and API response schema."""

from __future__ import annotations

import pytest

from mil.kernel.errors import (
    APIErrorDetail,
    APIErrorResponse,
    AuditWriteError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DependencyNotRegisteredError,
    DomainError,
    ErrorCode,
    ExplainabilityError,
    InvalidStateTransitionError,
    MILError,
    NotFoundError,
    ProvenanceError,
    ProviderError,
    ProviderVersionMissingError,
    ScopeViolationError,
    ValidationError,
)

# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    def test_domain_error_is_mil_error(self) -> None:
        assert issubclass(DomainError, MILError)

    def test_not_found_is_domain_error(self) -> None:
        assert issubclass(NotFoundError, DomainError)

    def test_validation_error_is_domain_error(self) -> None:
        assert issubclass(ValidationError, DomainError)

    def test_invalid_state_transition_is_domain_error(self) -> None:
        assert issubclass(InvalidStateTransitionError, DomainError)

    def test_conflict_is_domain_error(self) -> None:
        assert issubclass(ConflictError, DomainError)

    def test_provenance_error_is_domain_error(self) -> None:
        assert issubclass(ProvenanceError, DomainError)

    def test_explainability_error_is_domain_error(self) -> None:
        assert issubclass(ExplainabilityError, DomainError)

    def test_scope_violation_is_domain_error(self) -> None:
        assert issubclass(ScopeViolationError, DomainError)

    def test_auth_errors_are_mil_errors_not_domain(self) -> None:
        assert issubclass(AuthenticationError, MILError)
        assert issubclass(AuthorizationError, MILError)
        assert not issubclass(AuthenticationError, DomainError)
        assert not issubclass(AuthorizationError, DomainError)

    def test_provider_error_is_mil_error(self) -> None:
        assert issubclass(ProviderError, MILError)

    def test_provider_version_missing_is_provider_error(self) -> None:
        assert issubclass(ProviderVersionMissingError, ProviderError)

    def test_audit_write_error_is_mil_error(self) -> None:
        assert issubclass(AuditWriteError, MILError)

    def test_dependency_not_registered_is_mil_error(self) -> None:
        assert issubclass(DependencyNotRegisteredError, MILError)

    def test_all_mil_errors_are_exceptions(self) -> None:
        for cls in (
            MILError,
            DomainError,
            NotFoundError,
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            ProviderError,
            AuditWriteError,
        ):
            assert issubclass(cls, Exception)


# ---------------------------------------------------------------------------
# MILError base
# ---------------------------------------------------------------------------


class TestMILError:
    def test_message_and_code_stored(self) -> None:
        err = MILError("something went wrong", code="SOME_CODE")
        assert err.message == "something went wrong"
        assert err.code == "SOME_CODE"

    def test_details_defaults_to_empty_dict(self) -> None:
        err = MILError("msg", code="CODE")
        assert err.details == {}

    def test_details_provided(self) -> None:
        err = MILError("msg", code="CODE", details={"key": "value"})
        assert err.details["key"] == "value"

    def test_str_representation_is_message(self) -> None:
        err = MILError("my error", code="CODE")
        assert "my error" in str(err)

    def test_can_be_caught_as_exception(self) -> None:
        with pytest.raises(MILError):
            raise MILError("test", code="CODE")


# ---------------------------------------------------------------------------
# NotFoundError
# ---------------------------------------------------------------------------


class TestNotFoundError:
    def test_message_includes_entity_type_and_id(self) -> None:
        err = NotFoundError("Application", "abc-123")
        assert "Application" in err.message
        assert "abc-123" in err.message

    def test_error_code(self) -> None:
        err = NotFoundError("Finding", "xyz")
        assert err.code == ErrorCode.NOT_FOUND

    def test_details_include_entity_info(self) -> None:
        err = NotFoundError("Document", "doc-456")
        assert err.details["entity_type"] == "Document"
        assert "doc-456" in str(err.details["entity_id"])


# ---------------------------------------------------------------------------
# ValidationError
# ---------------------------------------------------------------------------


class TestValidationError:
    def test_basic(self) -> None:
        err = ValidationError("amount must be positive")
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert "amount must be positive" in err.message

    def test_field_stored_in_details(self) -> None:
        err = ValidationError("required", field="income")
        assert err.details.get("field") == "income"


# ---------------------------------------------------------------------------
# InvalidStateTransitionError
# ---------------------------------------------------------------------------


class TestInvalidStateTransitionError:
    def test_message_describes_transition(self) -> None:
        err = InvalidStateTransitionError(
            entity_type="Finding",
            entity_id="find-001",
            from_state="VERIFIED",
            to_state="EXTRACTED",
        )
        assert "VERIFIED" in err.message
        assert "EXTRACTED" in err.message

    def test_error_code(self) -> None:
        err = InvalidStateTransitionError("Finding", "x", "A", "B")
        assert err.code == ErrorCode.INVALID_STATE_TRANSITION

    def test_details_contain_states(self) -> None:
        err = InvalidStateTransitionError("Finding", "x", "VERIFIED", "EXTRACTED")
        assert err.details["from_state"] == "VERIFIED"
        assert err.details["to_state"] == "EXTRACTED"


# ---------------------------------------------------------------------------
# AuthorizationError
# ---------------------------------------------------------------------------


class TestAuthorizationError:
    def test_required_permission_stored(self) -> None:
        err = AuthorizationError("denied", required_permission="verify:finding")
        assert err.details.get("required_permission") == "verify:finding"

    def test_error_code(self) -> None:
        err = AuthorizationError("denied")
        assert err.code == ErrorCode.INSUFFICIENT_PERMISSIONS


# ---------------------------------------------------------------------------
# ProviderVersionMissingError
# ---------------------------------------------------------------------------


class TestProviderVersionMissingError:
    def test_message_includes_provider_and_field(self) -> None:
        err = ProviderVersionMissingError("DocuOCR", "model_version")
        assert "DocuOCR" in err.message
        assert "model_version" in err.message

    def test_error_code(self) -> None:
        err = ProviderVersionMissingError("DocuOCR", "model_version")
        assert err.code == ErrorCode.PROVIDER_VERSION_MISSING


# ---------------------------------------------------------------------------
# DependencyNotRegisteredError
# ---------------------------------------------------------------------------


class TestDependencyNotRegisteredError:
    def test_message_includes_interface_name(self) -> None:
        class MyInterface:
            pass

        err = DependencyNotRegisteredError(MyInterface)
        assert "MyInterface" in err.message

    def test_error_code(self) -> None:
        class MyInterface:
            pass

        err = DependencyNotRegisteredError(MyInterface)
        assert err.code == ErrorCode.DEPENDENCY_NOT_REGISTERED


# ---------------------------------------------------------------------------
# Error code constants
# ---------------------------------------------------------------------------


class TestErrorCode:
    def test_all_codes_are_strings(self) -> None:
        codes = [
            ErrorCode.NOT_FOUND,
            ErrorCode.VALIDATION_FAILED,
            ErrorCode.INVALID_STATE_TRANSITION,
            ErrorCode.CONFLICT,
            ErrorCode.EVIDENCE_PROVENANCE_INCOMPLETE,
            ErrorCode.FINDING_EXPLAINABILITY_INCOMPLETE,
            ErrorCode.EVIDENCE_SCOPE_VIOLATION,
            ErrorCode.POLICY_EVALUATION_FAILED,
            ErrorCode.AUTHENTICATION_REQUIRED,
            ErrorCode.INSUFFICIENT_PERMISSIONS,
            ErrorCode.PROVIDER_UNAVAILABLE,
            ErrorCode.PROVIDER_VERSION_MISSING,
            ErrorCode.AUDIT_WRITE_FAILED,
            ErrorCode.DEPENDENCY_NOT_REGISTERED,
        ]
        for code in codes:
            assert isinstance(code, str)
            assert len(code) > 0
            assert code == code.upper(), f"Code '{code}' should be SCREAMING_SNAKE_CASE"


# ---------------------------------------------------------------------------
# API error response schema
# ---------------------------------------------------------------------------


class TestAPIErrorResponse:
    def test_minimal_response(self) -> None:
        resp = APIErrorResponse(code="NOT_FOUND", message="not found")
        assert resp.code == "NOT_FOUND"
        assert resp.message == "not found"
        assert resp.request_id is None
        assert resp.details == []

    def test_with_request_id(self) -> None:
        resp = APIErrorResponse(code="X", message="y", request_id="req-123")
        assert resp.request_id == "req-123"

    def test_with_details(self) -> None:
        detail = APIErrorDetail(field="income", message="must be positive")
        resp = APIErrorResponse(code="X", message="y", details=[detail])
        assert len(resp.details) == 1
        assert resp.details[0].field == "income"

    def test_serialises_to_dict(self) -> None:
        resp = APIErrorResponse(code="NOT_FOUND", message="not found")
        data = resp.model_dump()
        assert data["code"] == "NOT_FOUND"
        assert "details" in data

    def test_serialises_to_json(self) -> None:
        resp = APIErrorResponse(code="X", message="y")
        json_str = resp.model_dump_json()
        assert '"code"' in json_str
        assert '"message"' in json_str
