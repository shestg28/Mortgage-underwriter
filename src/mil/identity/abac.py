"""
ABAC (Attribute-Based Access Control) policies for the Identity bounded context.

RBAC determines *which actions* a user may perform based on their role.
ABAC determines *which data* a user may access based on attributes of both
the user and the resource.

For MIL, the critical ABAC concerns are:

1. **Tenant isolation** — a user belonging to Tenant A must never access
   data owned by Tenant B, regardless of their role.

2. **Cross-application denial** — when a user is processing Application X,
   they must not access data associated with Application Y in the same
   request.  Evidence, Findings, and Documents are all scoped to a single
   application; a query that mixes application contexts is a data access
   violation.

These policies are enforced at the service layer *before* any database
query is executed, providing a defence-in-depth layer above the
database-level tenant column filtering.

Design:

- ``ABACPolicy`` — abstract base class for all ABAC policies.
- ``TenantScopePolicy`` — enforces tenant isolation.
- ``CrossApplicationDenialPolicy`` — enforces single-application scope.
- Module-level helpers ``enforce_tenant_scope`` and
  ``enforce_application_scope`` are the primary entry points used by
  service-layer code.

Dependency rule: imports only from ``mil.kernel`` and the Python standard
library.  No bounded context may be imported here.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from mil.kernel.errors import ScopeViolationError

if TYPE_CHECKING:
    from uuid import UUID

    from mil.kernel.security import AuthenticatedUser
    from mil.kernel.types import ApplicationId, TenantId


# ---------------------------------------------------------------------------
# Abstract base policy
# ---------------------------------------------------------------------------


class ABACPolicy(abc.ABC):
    """
    Abstract base for all ABAC policy classes.

    Each concrete policy enforces a single, well-named invariant.
    Service-layer code instantiates and calls ``enforce`` directly, or uses
    the module-level helper functions which wrap the default policies.
    """

    @abc.abstractmethod
    def enforce(self, user: AuthenticatedUser, **resource_attrs: object) -> None:
        """
        Enforce this policy for the given user and resource attributes.

        Raises:
            ScopeViolationError: If the policy rejects the access attempt.
        """


# ---------------------------------------------------------------------------
# Concrete policies
# ---------------------------------------------------------------------------


class TenantScopePolicy(ABACPolicy):
    """
    Enforce that the authenticated user belongs to the resource's tenant.

    Every resource in MIL is owned by exactly one tenant.  A user whose
    ``tenant_id`` does not match the resource's ``tenant_id`` must be
    denied access regardless of their RBAC roles, because roles are also
    tenant-scoped.

    This is the outer boundary of data isolation.
    """

    def enforce(self, user: AuthenticatedUser, **resource_attrs: object) -> None:
        """
        Args:
            user: The authenticated principal.
            resource_attrs: Must include ``resource_tenant_id: TenantId``.

        Raises:
            ScopeViolationError: If the user's tenant differs from the
                resource's tenant.
            ValueError: If ``resource_tenant_id`` is not provided.
        """
        resource_tenant_id: UUID | None = resource_attrs.get("resource_tenant_id")  # type: ignore[assignment]
        if resource_tenant_id is None:
            raise ValueError("TenantScopePolicy requires 'resource_tenant_id' attribute")

        if user.tenant_id != resource_tenant_id:
            raise ScopeViolationError(
                message="Tenant scope violation: access denied to resource outside caller's tenant",
                details={
                    "user_tenant_id": str(user.tenant_id),
                    "resource_tenant_id": str(resource_tenant_id),
                },
            )


class CrossApplicationDenialPolicy(ABACPolicy):
    """
    Enforce that a user's data access is scoped to a single application.

    When a request targets Application X, any data item associated with a
    different application must be inaccessible.  This prevents information
    leakage between applications in the same tenant — for example, a
    reviewer working on application A-001 must not see evidence from A-002.

    Usage::

        # In a service method that loads a Finding for a specific application:
        policy = CrossApplicationDenialPolicy()
        policy.enforce(
            user,
            requested_application_id=requested_app_id,
            resource_application_id=finding.application_id,
        )
    """

    def enforce(self, user: AuthenticatedUser, **resource_attrs: object) -> None:
        """
        Args:
            user: The authenticated principal (carried for audit purposes).
            resource_attrs: Must include:
                - ``requested_application_id: ApplicationId`` — the
                  application the caller declared in the request path.
                - ``resource_application_id: ApplicationId`` — the
                  application to which the resource actually belongs.

        Raises:
            ScopeViolationError: If the resource's application differs from
                the requested application.
            ValueError: If either required attribute is missing.
        """
        requested: UUID | None = resource_attrs.get("requested_application_id")  # type: ignore[assignment]
        resource: UUID | None = resource_attrs.get("resource_application_id")  # type: ignore[assignment]

        if requested is None:
            raise ValueError("CrossApplicationDenialPolicy requires 'requested_application_id'")
        if resource is None:
            raise ValueError("CrossApplicationDenialPolicy requires 'resource_application_id'")

        if requested != resource:
            raise ScopeViolationError(
                message=(
                    "Cross-application access denied: resource belongs to a different "
                    "application than the one declared in this request"
                ),
                details={
                    "requested_application_id": str(requested),
                    "resource_application_id": str(resource),
                    "user_id": str(user.user_id),
                },
            )


# ---------------------------------------------------------------------------
# Default policy singletons
# ---------------------------------------------------------------------------

_TENANT_POLICY = TenantScopePolicy()
_CROSS_APP_POLICY = CrossApplicationDenialPolicy()


# ---------------------------------------------------------------------------
# Module-level enforcement helpers
# ---------------------------------------------------------------------------


def enforce_tenant_scope(
    user: AuthenticatedUser,
    resource_tenant_id: TenantId,
) -> None:
    """
    Assert that the user's tenant matches the resource's tenant.

    This is the primary tenant-isolation check.  Call it at the start of
    any service method that loads or mutates a persisted resource::

        def get_application(user, app_id, session):
            app = session.get(Application, app_id)
            if app is None:
                raise NotFoundError("Application", app_id)
            enforce_tenant_scope(user, app.tenant_id)
            ...

    Raises:
        ScopeViolationError: If the user's tenant does not match the
            resource's tenant.
    """
    _TENANT_POLICY.enforce(user, resource_tenant_id=resource_tenant_id)


def enforce_application_scope(
    user: AuthenticatedUser,
    requested_application_id: ApplicationId,
    resource_application_id: ApplicationId,
) -> None:
    """
    Assert that the accessed resource belongs to the declared application.

    Call this before returning any application-scoped resource (Evidence,
    Finding, Document, Party) to prevent cross-application data leakage::

        def get_finding(user, application_id, finding_id, session):
            finding = session.get(Finding, finding_id)
            if finding is None:
                raise NotFoundError("Finding", finding_id)
            enforce_application_scope(user, application_id, finding.application_id)
            ...

    Raises:
        ScopeViolationError: If the resource's application does not match
            the requested application.
    """
    _CROSS_APP_POLICY.enforce(
        user,
        requested_application_id=requested_application_id,
        resource_application_id=resource_application_id,
    )
