"""
Request context propagation utilities for the MIL Platform.

Provides correlation ID generation and a per-request ``RequestContext``
dataclass that threads a unique correlation identifier through the async
request lifecycle without thread-local storage.

Usage pattern::

    # In request ingress middleware (T022):
    ctx = RequestContext(correlation_id=generate_correlation_id())
    token = set_request_context(ctx)
    try:
        await call_next(request)
    finally:
        _current_request_context.reset(token)

    # In service-layer code:
    ctx = get_request_context()
    logger.info("Processing", correlation_id=ctx.correlation_id)

The correlation ID propagated here is the same value written to the
``request_id`` field of ``TraceContext`` (``observability.py``) and the
``request_id`` field of ``LogContext``.  The telemetry middleware (T023)
is responsible for syncing both context variables from a single generated
correlation ID.

Dependency rule: this module imports only from the Python standard library.
No bounded context code should be imported here.
"""

from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Correlation ID
# ---------------------------------------------------------------------------


def generate_correlation_id() -> str:
    """Return a new random UUID4 string for use as a correlation ID."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Request context
# ---------------------------------------------------------------------------


@dataclass
class RequestContext:
    """
    Per-request context carrying the correlation ID and scoped identifiers.

    Populated at request ingress by the audit context middleware (T022).
    Available throughout the request lifecycle via ``get_request_context()``.

    Attributes:
        correlation_id:  UUID4 string uniquely identifying this request.
                         Auto-generated if not supplied.
        application_id:  Mortgage application being processed, if known.
        user_id:         Authenticated user performing the request, if known.
    """

    correlation_id: str = field(default_factory=generate_correlation_id)
    application_id: str = ""
    user_id: str = ""


_current_request_context: contextvars.ContextVar[RequestContext | None] = contextvars.ContextVar(
    "current_request_context", default=None
)


def set_request_context(ctx: RequestContext) -> contextvars.Token[RequestContext | None]:
    """
    Bind a ``RequestContext`` to the current execution context.

    Returns the reset token so the caller can restore the previous context
    (e.g. in tests or when processing nested async tasks).
    """
    return _current_request_context.set(ctx)


def get_request_context() -> RequestContext:
    """Return the request context for the current execution, or a blank default."""
    ctx = _current_request_context.get()
    return ctx if ctx is not None else RequestContext()


def reset_request_context(token: contextvars.Token[RequestContext | None]) -> None:
    """
    Restore the request context to its prior value.

    Pass the token returned by ``set_request_context``. Used by request
    middleware and the worker harness to unbind a context after the unit of
    work completes.
    """
    _current_request_context.reset(token)
