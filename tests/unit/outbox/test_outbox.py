"""Unit tests for mil.outbox — OutboxEvent, OutboxRepository, Relay."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from mil.kernel.events import WorkflowStarted
from mil.kernel.types import ApplicationId, TenantId, WorkflowRunId
from mil.outbox.models import OutboxEvent, OutboxStatus
from mil.outbox.relay import NoOpRelay, Relay
from mil.outbox.repository import OutboxRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(correlation_id: str = "corr-1") -> WorkflowStarted:
    return WorkflowStarted(
        tenant_id=TenantId(uuid4()),
        workflow_run_id=WorkflowRunId(uuid4()),
        application_id=ApplicationId(uuid4()),
        workflow_type="DOCUMENT_INGESTION",
        correlation_id=correlation_id,
    )


# ---------------------------------------------------------------------------
# OutboxEvent.from_domain_event
# ---------------------------------------------------------------------------


class TestFromDomainEvent:
    def test_starts_pending(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        assert row.status == OutboxStatus.PENDING

    def test_captures_event_id(self) -> None:
        event = _make_event()
        row = OutboxEvent.from_domain_event(event)
        assert row.event_id == event.event_id

    def test_captures_event_type_name(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        assert row.event_type == "WorkflowStarted"

    def test_captures_tenant_id(self) -> None:
        event = _make_event()
        row = OutboxEvent.from_domain_event(event)
        assert row.tenant_id == event.tenant_id

    def test_propagates_correlation_id(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event(correlation_id="corr-xyz"))
        assert row.correlation_id == "corr-xyz"

    def test_payload_is_serialised_dict(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        assert isinstance(row.payload, dict)
        assert row.payload["event_type"] == "WorkflowStarted"

    def test_records_occurred_at(self) -> None:
        event = _make_event()
        row = OutboxEvent.from_domain_event(event)
        assert row.occurred_at == event.occurred_at

    def test_not_published_initially(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        assert row.is_published is False
        assert row.published_at is None


# ---------------------------------------------------------------------------
# mark_published
# ---------------------------------------------------------------------------


class TestMarkPublished:
    def test_sets_status_published(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        row.mark_published()
        assert row.status == OutboxStatus.PUBLISHED

    def test_sets_published_at(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        row.mark_published()
        assert row.published_at is not None

    def test_is_published_true(self) -> None:
        row = OutboxEvent.from_domain_event(_make_event())
        row.mark_published()
        assert row.is_published is True


# ---------------------------------------------------------------------------
# OutboxRepository
# ---------------------------------------------------------------------------


class TestOutboxRepository:
    def test_add_persists_outbox_row(self) -> None:
        session = MagicMock()
        repo = OutboxRepository(session)
        row = repo.add(_make_event())
        session.add.assert_called_once_with(row)

    def test_add_returns_outbox_event(self) -> None:
        session = MagicMock()
        repo = OutboxRepository(session)
        row = repo.add(_make_event())
        assert isinstance(row, OutboxEvent)

    def test_add_does_not_commit(self) -> None:
        session = MagicMock()
        repo = OutboxRepository(session)
        repo.add(_make_event())
        session.commit.assert_not_called()

    def test_fetch_pending_returns_list(self) -> None:
        session = MagicMock()
        r1 = OutboxEvent.from_domain_event(_make_event())
        r2 = OutboxEvent.from_domain_event(_make_event())
        session.scalars.return_value = iter([r1, r2])
        repo = OutboxRepository(session)
        assert repo.fetch_pending() == [r1, r2]

    def test_get_by_event_id_returns_row(self) -> None:
        session = MagicMock()
        row = OutboxEvent.from_domain_event(_make_event())
        session.scalars.return_value.one_or_none.return_value = row
        repo = OutboxRepository(session)
        assert repo.get_by_event_id(row.event_id) is row

    def test_mark_published_updates_and_persists(self) -> None:
        session = MagicMock()
        row = OutboxEvent.from_domain_event(_make_event())
        repo = OutboxRepository(session)
        repo.mark_published(row)
        assert row.status == OutboxStatus.PUBLISHED
        session.add.assert_called_once_with(row)


# ---------------------------------------------------------------------------
# Relay abstraction
# ---------------------------------------------------------------------------


class TestRelay:
    def test_relay_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            Relay()  # type: ignore[abstract]

    def test_noop_relay_publishes_nothing(self) -> None:
        relay = NoOpRelay()
        assert relay.relay_pending() == 0

    def test_noop_relay_is_a_relay(self) -> None:
        assert isinstance(NoOpRelay(), Relay)

    def test_noop_relay_respects_limit_arg(self) -> None:
        relay = NoOpRelay()
        assert relay.relay_pending(limit=10) == 0
