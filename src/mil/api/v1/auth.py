"""
Authentication and system health endpoints — MIL API v1.

Endpoints:
    GET /v1/health    — Liveness probe; no authentication required.
    GET /v1/me        — Return the authenticated caller's identity claims.

These endpoints are intentionally minimal.  ``/v1/health`` is a Kubernetes
liveness probe target; it must never require authentication or hit the database.
``/v1/me`` allows a client to verify its token and introspect its own permissions.

Dependency rule: imports from ``mil.api.deps``, ``mil.api.v1.schemas``, and
FastAPI only.  No business service is called.
"""

from __future__ import annotations

from fastapi import APIRouter

from mil.api.deps import CurrentUser  # noqa: TC001
from mil.api.v1.schemas import CurrentUserResponse, HealthResponse

router = APIRouter(tags=["System"])


@router.get(
    "/v1/health",
    summary="Health check",
    description=(
        "Liveness probe endpoint. Returns ``ok`` when the API process is "
        "running. Does not check database or provider connectivity. "
        "No authentication required."
    ),
    response_model=HealthResponse,
    status_code=200,
)
def health_check() -> HealthResponse:
    """Return API process health status."""
    return HealthResponse()


@router.get(
    "/v1/me",
    summary="Current authenticated user",
    description=(
        "Return the identity claims of the authenticated caller. "
        "Useful for clients to verify token validity and inspect role assignments."
    ),
    response_model=CurrentUserResponse,
    responses={
        401: {"description": "Authentication required"},
    },
)
def get_me(user: CurrentUser) -> CurrentUserResponse:
    """Return the authenticated caller's identity."""
    return CurrentUserResponse(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        roles=sorted(user.roles),
        email=user.email,
        display_name=user.display_name,
    )
