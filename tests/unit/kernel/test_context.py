"""Unit tests for mil.kernel.context — correlation ID and request context."""

from __future__ import annotations

from uuid import UUID

from mil.kernel.context import (
    RequestContext,
    _current_request_context,
    generate_correlation_id,
    get_request_context,
    set_request_context,
)

# ---------------------------------------------------------------------------
# generate_correlation_id
# ---------------------------------------------------------------------------


class TestGenerateCorrelationId:
    def test_returns_string(self) -> None:
        cid = generate_correlation_id()
        assert isinstance(cid, str)

    def test_is_valid_uuid4(self) -> None:
        cid = generate_correlation_id()
        parsed = UUID(cid)  # should not raise
        assert parsed.version == 4

    def test_unique_values(self) -> None:
        ids = {generate_correlation_id() for _ in range(100)}
        assert len(ids) == 100


# ---------------------------------------------------------------------------
# RequestContext
# ---------------------------------------------------------------------------


class TestRequestContext:
    def test_auto_generates_correlation_id(self) -> None:
        ctx = RequestContext()
        assert isinstance(ctx.correlation_id, str)
        assert len(ctx.correlation_id) == 36

    def test_correlation_id_unique_per_instance(self) -> None:
        a = RequestContext()
        b = RequestContext()
        assert a.correlation_id != b.correlation_id

    def test_application_id_defaults_empty(self) -> None:
        ctx = RequestContext()
        assert ctx.application_id == ""

    def test_user_id_defaults_empty(self) -> None:
        ctx = RequestContext()
        assert ctx.user_id == ""

    def test_custom_correlation_id_accepted(self) -> None:
        cid = "my-correlation-id"
        ctx = RequestContext(correlation_id=cid)
        assert ctx.correlation_id == cid

    def test_all_fields_settable(self) -> None:
        ctx = RequestContext(
            correlation_id="corr-001",
            application_id="app-001",
            user_id="user-001",
        )
        assert ctx.correlation_id == "corr-001"
        assert ctx.application_id == "app-001"
        assert ctx.user_id == "user-001"

    def test_fields_mutable(self) -> None:
        ctx = RequestContext()
        ctx.application_id = "app-001"
        assert ctx.application_id == "app-001"


# ---------------------------------------------------------------------------
# Context variable — set and get
# ---------------------------------------------------------------------------


class TestRequestContextVar:
    def test_default_returns_fresh_context(self) -> None:
        ctx = get_request_context()
        assert isinstance(ctx, RequestContext)

    def test_set_and_get_round_trip(self) -> None:
        ctx = RequestContext(correlation_id="test-corr-id")
        token = set_request_context(ctx)
        try:
            retrieved = get_request_context()
            assert retrieved is ctx
            assert retrieved.correlation_id == "test-corr-id"
        finally:
            _current_request_context.reset(token)

    def test_reset_restores_previous_state(self) -> None:
        ctx = RequestContext(correlation_id="temp-id")
        token = set_request_context(ctx)
        _current_request_context.reset(token)
        # After reset, get_request_context returns a fresh default (not the set ctx).
        fresh = get_request_context()
        assert fresh is not ctx

    def test_get_returns_default_when_not_set(self) -> None:
        # Ensure no token is active by resetting to None.
        token = _current_request_context.set(None)
        try:
            ctx = get_request_context()
            assert isinstance(ctx, RequestContext)
        finally:
            _current_request_context.reset(token)

    def test_nested_contexts_restore_correctly(self) -> None:
        outer = RequestContext(correlation_id="outer")
        inner = RequestContext(correlation_id="inner")

        outer_token = set_request_context(outer)
        assert get_request_context().correlation_id == "outer"

        inner_token = set_request_context(inner)
        assert get_request_context().correlation_id == "inner"

        _current_request_context.reset(inner_token)
        assert get_request_context().correlation_id == "outer"

        _current_request_context.reset(outer_token)
