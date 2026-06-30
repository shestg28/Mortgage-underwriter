"""Unit tests for mil.identity.abac — ABAC policy enforcement."""

from __future__ import annotations

from uuid import uuid4

import pytest

from mil.identity.abac import (
    CrossApplicationDenialPolicy,
    TenantScopePolicy,
    enforce_application_scope,
    enforce_tenant_scope,
)
from mil.kernel.errors import ScopeViolationError
from mil.kernel.security import AuthenticatedUser, Role
from mil.kernel.types import ApplicationId, TenantId, UserId

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def make_user(*roles: str, tenant_id: TenantId | None = None) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=UserId(uuid4()),
        tenant_id=tenant_id or TenantId(uuid4()),
        roles=frozenset(roles),
    )


# ---------------------------------------------------------------------------
# TenantScopePolicy
# ---------------------------------------------------------------------------


class TestTenantScopePolicy:
    def setup_method(self) -> None:
        self.policy = TenantScopePolicy()

    def test_same_tenant_passes(self) -> None:
        tid = TenantId(uuid4())
        user = make_user(Role.VERIFICATION_OFFICER, tenant_id=tid)
        self.policy.enforce(user, resource_tenant_id=tid)  # should not raise

    def test_different_tenant_raises(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER, tenant_id=TenantId(uuid4()))
        other_tenant = TenantId(uuid4())
        with pytest.raises(ScopeViolationError) as exc_info:
            self.policy.enforce(user, resource_tenant_id=other_tenant)
        assert "tenant" in exc_info.value.message.lower()

    def test_error_detail_contains_both_tenant_ids(self) -> None:
        user_tid = TenantId(uuid4())
        resource_tid = TenantId(uuid4())
        user = make_user(Role.AUDIT_TEAM, tenant_id=user_tid)
        with pytest.raises(ScopeViolationError) as exc_info:
            self.policy.enforce(user, resource_tenant_id=resource_tid)
        details = exc_info.value.details
        assert str(user_tid) in details.get("user_tenant_id", "")
        assert str(resource_tid) in details.get("resource_tenant_id", "")

    def test_missing_attribute_raises_value_error(self) -> None:
        user = make_user(Role.ADMIN)
        with pytest.raises(ValueError, match="resource_tenant_id"):
            self.policy.enforce(user)


# ---------------------------------------------------------------------------
# CrossApplicationDenialPolicy
# ---------------------------------------------------------------------------


class TestCrossApplicationDenialPolicy:
    def setup_method(self) -> None:
        self.policy = CrossApplicationDenialPolicy()

    def test_same_application_passes(self) -> None:
        app_id = ApplicationId(uuid4())
        user = make_user(Role.VERIFICATION_OFFICER)
        self.policy.enforce(
            user,
            requested_application_id=app_id,
            resource_application_id=app_id,
        )  # should not raise

    def test_different_application_raises(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        app_a = ApplicationId(uuid4())
        app_b = ApplicationId(uuid4())
        with pytest.raises(ScopeViolationError) as exc_info:
            self.policy.enforce(
                user,
                requested_application_id=app_a,
                resource_application_id=app_b,
            )
        assert "cross-application" in exc_info.value.message.lower()

    def test_error_detail_contains_application_ids(self) -> None:
        user = make_user(Role.UNDERWRITER)
        app_a = ApplicationId(uuid4())
        app_b = ApplicationId(uuid4())
        with pytest.raises(ScopeViolationError) as exc_info:
            self.policy.enforce(
                user,
                requested_application_id=app_a,
                resource_application_id=app_b,
            )
        details = exc_info.value.details
        assert str(app_a) in details.get("requested_application_id", "")
        assert str(app_b) in details.get("resource_application_id", "")

    def test_missing_requested_application_raises(self) -> None:
        user = make_user(Role.ADMIN)
        with pytest.raises(ValueError, match="requested_application_id"):
            self.policy.enforce(user, resource_application_id=ApplicationId(uuid4()))

    def test_missing_resource_application_raises(self) -> None:
        user = make_user(Role.ADMIN)
        with pytest.raises(ValueError, match="resource_application_id"):
            self.policy.enforce(user, requested_application_id=ApplicationId(uuid4()))

    def test_error_includes_user_id(self) -> None:
        user = make_user(Role.CREDIT_ANALYST)
        with pytest.raises(ScopeViolationError) as exc_info:
            self.policy.enforce(
                user,
                requested_application_id=ApplicationId(uuid4()),
                resource_application_id=ApplicationId(uuid4()),
            )
        assert str(user.user_id) in exc_info.value.details.get("user_id", "")


# ---------------------------------------------------------------------------
# enforce_tenant_scope helper
# ---------------------------------------------------------------------------


class TestEnforceTenantScope:
    def test_matching_tenant_passes(self) -> None:
        tid = TenantId(uuid4())
        user = make_user(Role.UNDERWRITER, tenant_id=tid)
        enforce_tenant_scope(user, tid)  # no exception

    def test_mismatched_tenant_raises_scope_violation(self) -> None:
        user = make_user(Role.UNDERWRITER, tenant_id=TenantId(uuid4()))
        with pytest.raises(ScopeViolationError):
            enforce_tenant_scope(user, TenantId(uuid4()))

    def test_error_code_is_scope_violation(self) -> None:
        from mil.kernel.errors import ErrorCode

        user = make_user(Role.AUDIT_TEAM, tenant_id=TenantId(uuid4()))
        with pytest.raises(ScopeViolationError) as exc_info:
            enforce_tenant_scope(user, TenantId(uuid4()))
        assert exc_info.value.code == ErrorCode.EVIDENCE_SCOPE_VIOLATION


# ---------------------------------------------------------------------------
# enforce_application_scope helper
# ---------------------------------------------------------------------------


class TestEnforceApplicationScope:
    def test_same_application_passes(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        app_id = ApplicationId(uuid4())
        enforce_application_scope(user, app_id, app_id)  # no exception

    def test_different_application_raises(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        with pytest.raises(ScopeViolationError):
            enforce_application_scope(
                user,
                ApplicationId(uuid4()),
                ApplicationId(uuid4()),
            )

    def test_consistent_with_policy_class(self) -> None:
        user = make_user(Role.COMPLIANCE_OFFICER)
        app_a = ApplicationId(uuid4())
        app_b = ApplicationId(uuid4())
        policy = CrossApplicationDenialPolicy()

        with pytest.raises(ScopeViolationError) as helper_exc:
            enforce_application_scope(user, app_a, app_b)
        with pytest.raises(ScopeViolationError) as policy_exc:
            policy.enforce(
                user,
                requested_application_id=app_a,
                resource_application_id=app_b,
            )
        assert helper_exc.value.code == policy_exc.value.code
