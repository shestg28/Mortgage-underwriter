"""Unit tests for mil.kernel.security — RBAC types and permission checks."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from mil.kernel.errors import AuthorizationError
from mil.kernel.security import (
    ROLE_PERMISSIONS,
    AuthenticatedUser,
    Permission,
    Role,
    current_user,
    has_permission,
    has_role,
    require_permission,
    set_current_user,
)
from mil.kernel.types import TenantId, UserId

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def make_user(
    *roles: str,
    email: str = "test@example.com",
    display_name: str = "Test User",
) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=UserId(uuid4()),
        tenant_id=TenantId(uuid4()),
        roles=frozenset(roles),
        email=email,
        display_name=display_name,
    )


# ---------------------------------------------------------------------------
# AuthenticatedUser
# ---------------------------------------------------------------------------


class TestAuthenticatedUser:
    def test_create_user(self) -> None:
        uid = UserId(uuid4())
        tid = TenantId(uuid4())
        user = AuthenticatedUser(user_id=uid, tenant_id=tid)
        assert user.user_id == uid
        assert user.tenant_id == tid

    def test_roles_default_to_empty_frozenset(self) -> None:
        user = make_user()
        assert user.roles == frozenset()

    def test_roles_stored_as_frozenset(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER, Role.UNDERWRITER)
        assert isinstance(user.roles, frozenset)
        assert Role.VERIFICATION_OFFICER in user.roles

    def test_email_and_display_name(self) -> None:
        user = make_user(email="alice@bank.com", display_name="Alice")
        assert user.email == "alice@bank.com"
        assert user.display_name == "Alice"

    def test_is_immutable(self) -> None:
        user = make_user(Role.AUDIT_TEAM)
        with pytest.raises(FrozenInstanceError):
            user.email = "hacker@evil.com"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------


class TestRoleConstants:
    def test_all_roles_are_strings(self) -> None:
        roles = [
            Role.VERIFICATION_OFFICER,
            Role.UNDERWRITER,
            Role.CREDIT_ANALYST,
            Role.RISK_ANALYST,
            Role.COMPLIANCE_OFFICER,
            Role.AUDIT_TEAM,
            Role.OPERATIONS_MANAGER,
            Role.RELATIONSHIP_MANAGER,
            Role.ADMIN,
            Role.SERVICE_ACCOUNT,
        ]
        for role in roles:
            assert isinstance(role, str)
            assert len(role) > 0

    def test_all_roles_are_screaming_snake_case(self) -> None:
        roles = [
            Role.VERIFICATION_OFFICER,
            Role.UNDERWRITER,
            Role.CREDIT_ANALYST,
            Role.AUDIT_TEAM,
        ]
        for role in roles:
            assert role == role.upper()


# ---------------------------------------------------------------------------
# Permission constants
# ---------------------------------------------------------------------------


class TestPermissionConstants:
    def test_permissions_follow_action_resource_convention(self) -> None:
        permissions = [
            Permission.READ_APPLICATION,
            Permission.WRITE_APPLICATION,
            Permission.READ_EVIDENCE,
            Permission.VERIFY_FINDING,
            Permission.OVERRIDE_FINDING,
            Permission.READ_AUDIT,
        ]
        for perm in permissions:
            assert ":" in perm, f"Permission '{perm}' should follow 'action:resource' format"

    def test_admin_permission_exists(self) -> None:
        assert Permission.ADMIN == "admin"


# ---------------------------------------------------------------------------
# has_role
# ---------------------------------------------------------------------------


class TestHasRole:
    def test_user_with_role(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        assert has_role(user, Role.VERIFICATION_OFFICER) is True

    def test_user_without_role(self) -> None:
        user = make_user(Role.CREDIT_ANALYST)
        assert has_role(user, Role.ADMIN) is False

    def test_user_with_multiple_roles(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER, Role.UNDERWRITER)
        assert has_role(user, Role.VERIFICATION_OFFICER) is True
        assert has_role(user, Role.UNDERWRITER) is True
        assert has_role(user, Role.ADMIN) is False

    def test_user_with_no_roles(self) -> None:
        user = make_user()
        assert has_role(user, Role.VERIFICATION_OFFICER) is False


# ---------------------------------------------------------------------------
# has_permission
# ---------------------------------------------------------------------------


class TestHasPermission:
    def test_verification_officer_can_verify_findings(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        assert has_permission(user, Permission.VERIFY_FINDING) is True

    def test_relationship_manager_cannot_verify_findings(self) -> None:
        user = make_user(Role.RELATIONSHIP_MANAGER)
        assert has_permission(user, Permission.VERIFY_FINDING) is False

    def test_audit_team_can_read_audit(self) -> None:
        user = make_user(Role.AUDIT_TEAM)
        assert has_permission(user, Permission.READ_AUDIT) is True

    def test_verification_officer_cannot_read_audit(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        assert has_permission(user, Permission.READ_AUDIT) is False

    def test_admin_granted_all_permissions(self) -> None:
        user = make_user(Role.ADMIN)
        for perm in (
            Permission.READ_APPLICATION,
            Permission.VERIFY_FINDING,
            Permission.READ_AUDIT,
            Permission.MANAGE_USERS,
        ):
            assert has_permission(user, perm) is True, f"Admin should have '{perm}'"

    def test_user_with_no_roles_has_no_permissions(self) -> None:
        user = make_user()
        assert has_permission(user, Permission.READ_APPLICATION) is False

    def test_multi_role_user_union_of_permissions(self) -> None:
        # CREDIT_ANALYST cannot override; UNDERWRITER can
        user = make_user(Role.CREDIT_ANALYST, Role.UNDERWRITER)
        assert has_permission(user, Permission.OVERRIDE_FINDING) is True


# ---------------------------------------------------------------------------
# require_permission
# ---------------------------------------------------------------------------


class TestRequirePermission:
    def test_no_exception_when_permitted(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        require_permission(user, Permission.VERIFY_FINDING)  # should not raise

    def test_raises_authorization_error_when_denied(self) -> None:
        user = make_user(Role.RELATIONSHIP_MANAGER)
        with pytest.raises(AuthorizationError) as exc_info:
            require_permission(user, Permission.VERIFY_FINDING)
        assert "verify:finding" in exc_info.value.message

    def test_error_contains_required_permission(self) -> None:
        user = make_user(Role.CREDIT_ANALYST)
        with pytest.raises(AuthorizationError) as exc_info:
            require_permission(user, Permission.OVERRIDE_FINDING)
        assert exc_info.value.details.get("required_permission") == Permission.OVERRIDE_FINDING


# ---------------------------------------------------------------------------
# ROLE_PERMISSIONS mapping
# ---------------------------------------------------------------------------


class TestRolePermissionMap:
    def test_all_defined_roles_have_entries(self) -> None:
        defined_roles = {
            Role.RELATIONSHIP_MANAGER,
            Role.VERIFICATION_OFFICER,
            Role.CREDIT_ANALYST,
            Role.UNDERWRITER,
            Role.RISK_ANALYST,
            Role.COMPLIANCE_OFFICER,
            Role.AUDIT_TEAM,
            Role.OPERATIONS_MANAGER,
            Role.ADMIN,
            Role.SERVICE_ACCOUNT,
        }
        for role in defined_roles:
            assert role in ROLE_PERMISSIONS, f"Role '{role}' missing from ROLE_PERMISSIONS"

    def test_permission_sets_are_frozensets(self) -> None:
        for role, perms in ROLE_PERMISSIONS.items():
            assert isinstance(perms, frozenset), f"Permissions for '{role}' should be a frozenset"

    def test_every_permission_set_is_non_empty(self) -> None:
        for role, perms in ROLE_PERMISSIONS.items():
            assert len(perms) > 0, f"Role '{role}' has no permissions"


# ---------------------------------------------------------------------------
# Context variable
# ---------------------------------------------------------------------------


class TestCurrentUserContextVar:
    def test_current_user_none_by_default(self) -> None:
        assert current_user() is None

    def test_set_and_get_current_user(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        token = set_current_user(user)
        try:
            retrieved = current_user()
            assert retrieved is user
        finally:
            from mil.kernel.security import _current_user_var

            _current_user_var.reset(token)

    def test_reset_restores_previous_value(self) -> None:
        user = make_user(Role.AUDIT_TEAM)
        token = set_current_user(user)
        from mil.kernel.security import _current_user_var

        _current_user_var.reset(token)
        assert current_user() is None
