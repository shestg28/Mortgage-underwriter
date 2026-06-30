"""Unit tests for mil.identity.rbac — FastAPI-compatible RBAC enforcement."""

from __future__ import annotations

from uuid import uuid4

import pytest

from mil.identity.rbac import (
    get_authenticated_user,
    permission_required,
    roles_required,
)
from mil.kernel.errors import AuthenticationError, AuthorizationError
from mil.kernel.security import (
    AuthenticatedUser,
    Permission,
    Role,
    _current_user_var,
    set_current_user,
)
from mil.kernel.types import TenantId, UserId

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def make_user(*roles: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=UserId(uuid4()),
        tenant_id=TenantId(uuid4()),
        roles=frozenset(roles),
        email="test@example.com",
        display_name="Test User",
    )


class _BoundContextVar:
    """Context manager that binds a user into the context variable."""

    def __init__(self, user: AuthenticatedUser) -> None:
        self._user = user
        self._token = None

    def __enter__(self) -> AuthenticatedUser:
        self._token = set_current_user(self._user)
        return self._user

    def __exit__(self, *_: object) -> None:
        if self._token is not None:
            _current_user_var.reset(self._token)


# ---------------------------------------------------------------------------
# get_authenticated_user
# ---------------------------------------------------------------------------


class TestGetAuthenticatedUser:
    def test_returns_user_when_context_set(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        with _BoundContextVar(user):
            result = get_authenticated_user()
        assert result is user

    def test_raises_when_no_context(self) -> None:
        # Ensure context variable is empty by resetting it.
        token = _current_user_var.set(None)
        try:
            with pytest.raises(AuthenticationError):
                get_authenticated_user()
        finally:
            _current_user_var.reset(token)


# ---------------------------------------------------------------------------
# permission_required
# ---------------------------------------------------------------------------


class TestPermissionRequired:
    def test_returns_user_when_permission_granted(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        with _BoundContextVar(user):
            dep = permission_required(Permission.VERIFY_FINDING)
            result = dep()
        assert result is user

    def test_raises_authorization_error_when_denied(self) -> None:
        user = make_user(Role.RELATIONSHIP_MANAGER)
        with _BoundContextVar(user):
            dep = permission_required(Permission.VERIFY_FINDING)
            with pytest.raises(AuthorizationError):
                dep()

    def test_raises_authentication_error_when_no_context(self) -> None:
        token = _current_user_var.set(None)
        try:
            dep = permission_required(Permission.READ_APPLICATION)
            with pytest.raises(AuthenticationError):
                dep()
        finally:
            _current_user_var.reset(token)

    def test_admin_bypasses_permission_check(self) -> None:
        user = make_user(Role.ADMIN)
        with _BoundContextVar(user):
            dep = permission_required(Permission.READ_AUDIT)
            result = dep()
        assert result is user

    def test_returned_callable_has_descriptive_name(self) -> None:
        dep = permission_required(Permission.READ_APPLICATION)
        assert "read" in dep.__name__
        assert "application" in dep.__name__

    def test_multi_role_user_union_grants_permission(self) -> None:
        # CREDIT_ANALYST cannot override; UNDERWRITER can.
        user = make_user(Role.CREDIT_ANALYST, Role.UNDERWRITER)
        with _BoundContextVar(user):
            dep = permission_required(Permission.OVERRIDE_FINDING)
            result = dep()
        assert result is user

    def test_different_permissions_create_independent_callables(self) -> None:
        dep_read = permission_required(Permission.READ_APPLICATION)
        dep_write = permission_required(Permission.WRITE_APPLICATION)
        assert dep_read is not dep_write

    def test_verify_finding_permission_for_verification_officer(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        with _BoundContextVar(user):
            dep = permission_required(Permission.VERIFY_FINDING)
            dep()  # should not raise

    def test_audit_team_can_read_audit(self) -> None:
        user = make_user(Role.AUDIT_TEAM)
        with _BoundContextVar(user):
            dep = permission_required(Permission.READ_AUDIT)
            dep()  # should not raise

    def test_audit_team_cannot_override_finding(self) -> None:
        user = make_user(Role.AUDIT_TEAM)
        with _BoundContextVar(user):
            dep = permission_required(Permission.OVERRIDE_FINDING)
            with pytest.raises(AuthorizationError):
                dep()


# ---------------------------------------------------------------------------
# roles_required
# ---------------------------------------------------------------------------


class TestRolesRequired:
    def test_returns_user_when_role_present(self) -> None:
        user = make_user(Role.ADMIN)
        with _BoundContextVar(user):
            dep = roles_required(Role.ADMIN)
            result = dep()
        assert result is user

    def test_raises_when_role_absent(self) -> None:
        user = make_user(Role.VERIFICATION_OFFICER)
        with _BoundContextVar(user):
            dep = roles_required(Role.ADMIN)
            with pytest.raises(AuthorizationError) as exc_info:
                dep()
        assert "ADMIN" in exc_info.value.message

    def test_satisfies_any_one_of_multiple_roles(self) -> None:
        user = make_user(Role.UNDERWRITER)
        with _BoundContextVar(user):
            dep = roles_required(Role.ADMIN, Role.UNDERWRITER)
            result = dep()
        assert result is user

    def test_raises_when_none_of_multiple_roles_present(self) -> None:
        user = make_user(Role.CREDIT_ANALYST)
        with _BoundContextVar(user):
            dep = roles_required(Role.ADMIN, Role.UNDERWRITER)
            with pytest.raises(AuthorizationError):
                dep()

    def test_raises_when_no_roles_argument(self) -> None:
        with pytest.raises(ValueError, match="requires at least one role"):
            roles_required()

    def test_raises_authentication_error_when_no_context(self) -> None:
        token = _current_user_var.set(None)
        try:
            dep = roles_required(Role.ADMIN)
            with pytest.raises(AuthenticationError):
                dep()
        finally:
            _current_user_var.reset(token)

    def test_returned_callable_has_descriptive_name(self) -> None:
        dep = roles_required(Role.ADMIN)
        assert "ADMIN" in dep.__name__
