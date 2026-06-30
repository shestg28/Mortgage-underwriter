"""
RBAC enforcement for the Identity bounded context.

This module bridges the kernel-level RBAC primitives (defined in
``mil.kernel.security``) and the FastAPI request lifecycle by providing
dependency-injectable enforcement helpers.

The kernel defines *what* the permission model is.  This module defines
*how* that model is enforced in FastAPI endpoints.

Design:

- ``get_authenticated_user()`` — resolves the current ``AuthenticatedUser``
  from the request context variable populated by the auth middleware.
  Raises ``AuthenticationError`` if no user is present.

- ``permission_required(permission)`` — returns a FastAPI
  ``Depends``-compatible callable that enforces a single permission.
  Endpoints declare their required permission as a default parameter::

      @router.get("/applications/{id}")
      async def get_application(
          application_id: UUID,
          user: AuthenticatedUser = permission_required(Permission.READ_APPLICATION),
      ) -> ApplicationResponse:
          ...

- ``roles_required(*roles)`` — enforces that the caller holds at least
  one of the specified roles.  Use this when the access control decision
  is role-based rather than permission-based.

Dependency rule: imports only from ``mil.kernel`` and the Python standard
library.  No bounded context may be imported here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mil.kernel.errors import AuthenticationError

if TYPE_CHECKING:
    from collections.abc import Callable
from mil.kernel.security import (
    AuthenticatedUser,
    current_user,
    has_permission,
    has_role,
)
from mil.kernel.security import (
    require_permission as kernel_require_permission,
)

# Re-export kernel helpers so callers can import everything from one place.
__all__ = [
    "get_authenticated_user",
    "has_permission",
    "has_role",
    "permission_required",
    "roles_required",
]


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------


def get_authenticated_user() -> AuthenticatedUser:
    """
    Return the current ``AuthenticatedUser`` from the request context.

    Raises:
        AuthenticationError: If the authentication middleware has not
            populated the context variable (unauthenticated request).
    """
    user = current_user()
    if user is None:
        raise AuthenticationError(
            "Request context contains no authenticated user. "
            "Ensure the Zero Trust authentication middleware is registered."
        )
    return user


# ---------------------------------------------------------------------------
# FastAPI dependency factories
# ---------------------------------------------------------------------------


def permission_required(permission: str) -> Callable[[], AuthenticatedUser]:
    """
    Return a FastAPI dependency that enforces a single permission.

    The returned callable resolves the current ``AuthenticatedUser``,
    checks the specified permission, and either returns the user (for
    injection into the endpoint) or raises ``AuthorizationError``.

    Usage::

        @router.delete("/applications/{id}")
        async def delete_application(
            user: AuthenticatedUser = permission_required(Permission.WRITE_APPLICATION),
        ) -> None:
            ...

    Args:
        permission: A ``Permission`` constant (e.g. ``Permission.READ_APPLICATION``).

    Returns:
        A no-argument callable compatible with ``fastapi.Depends``.
    """

    def _enforce() -> AuthenticatedUser:
        user = get_authenticated_user()
        kernel_require_permission(user, permission)
        return user

    # Set a descriptive function name so FastAPI OpenAPI docs can surface it.
    _enforce.__name__ = f"require_{permission.replace(':', '_')}"
    return _enforce


def roles_required(*roles: str) -> Callable[[], AuthenticatedUser]:
    """
    Return a FastAPI dependency that enforces membership in at least one role.

    The caller must hold *at least one* of the specified roles.  Use this
    when the decision is role-based (e.g. "only ADMIN may create tenants")
    rather than permission-based.

    For most access control decisions, prefer ``permission_required`` —
    checking permissions rather than roles insulates business logic from
    RBAC mapping changes.

    Args:
        *roles: One or more ``Role`` constants.

    Returns:
        A no-argument callable compatible with ``fastapi.Depends``.
    """
    if not roles:
        raise ValueError("roles_required() requires at least one role argument")

    role_set = frozenset(roles)

    def _enforce() -> AuthenticatedUser:
        user = get_authenticated_user()
        if not any(has_role(user, r) for r in role_set):
            from mil.kernel.errors import AuthorizationError

            role_list = ", ".join(sorted(role_set))
            raise AuthorizationError(
                message=f"One of the following roles is required: {role_list}",
                details={"required_roles": sorted(role_set)},
            )
        return user

    _enforce.__name__ = f"require_role_{'_or_'.join(sorted(roles))}"
    return _enforce
