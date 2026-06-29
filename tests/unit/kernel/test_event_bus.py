"""Unit tests for mil.kernel.event_bus — EventBus interface and InProcessEventBus."""

from __future__ import annotations

from uuid import uuid4

import pytest

from mil.kernel.event_bus import EventBus, EventHandler, InProcessEventBus
from mil.kernel.events import DocumentIngested, DomainEvent, FindingGenerated
from mil.kernel.types import ApplicationId, DocumentId, FindingId, TenantId

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_tenant_id() -> TenantId:
    return TenantId(uuid4())


def make_document_ingested() -> DocumentIngested:
    return DocumentIngested(
        tenant_id=make_tenant_id(),
        document_id=DocumentId(uuid4()),
        application_id=ApplicationId(uuid4()),
        storage_reference="s3://bucket/doc",
        content_hash="sha256:abc",
    )


def make_finding_generated() -> FindingGenerated:
    return FindingGenerated(
        tenant_id=make_tenant_id(),
        finding_id=FindingId(uuid4()),
        application_id=ApplicationId(uuid4()),
        finding_type="income_verification",
        policy_version="1.0.0",
    )


# ---------------------------------------------------------------------------
# EventBus interface contract
# ---------------------------------------------------------------------------


class TestEventBusInterface:
    def test_in_process_is_event_bus(self) -> None:
        bus = InProcessEventBus()
        assert isinstance(bus, EventBus)

    def test_event_bus_is_abstract(self) -> None:
        import inspect

        assert inspect.isabstract(EventBus)

    def test_abstract_methods(self) -> None:
        assert "publish" in EventBus.__abstractmethods__
        assert "subscribe" in EventBus.__abstractmethods__
        assert "unsubscribe" in EventBus.__abstractmethods__
        assert "subscriber_count" in EventBus.__abstractmethods__


# ---------------------------------------------------------------------------
# EventHandler protocol
# ---------------------------------------------------------------------------


class TestEventHandlerProtocol:
    def test_callable_satisfies_protocol(self) -> None:
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        assert isinstance(handler, EventHandler)

    def test_lambda_satisfies_protocol(self) -> None:
        assert isinstance(lambda e: None, EventHandler)


# ---------------------------------------------------------------------------
# InProcessEventBus — subscribe and publish
# ---------------------------------------------------------------------------


class TestInProcessEventBusSubscribePublish:
    def test_handler_called_on_matching_event(self) -> None:
        bus = InProcessEventBus()
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(DocumentIngested, handler)
        event = make_document_ingested()
        bus.publish(event)

        assert len(received) == 1
        assert received[0] is event

    def test_handler_not_called_for_different_event_type(self) -> None:
        bus = InProcessEventBus()
        received: list[DomainEvent] = []

        bus.subscribe(DocumentIngested, lambda e: received.append(e))
        bus.publish(make_finding_generated())

        assert received == []

    def test_multiple_handlers_all_called(self) -> None:
        bus = InProcessEventBus()
        calls: list[str] = []

        bus.subscribe(DocumentIngested, lambda e: calls.append("h1"))
        bus.subscribe(DocumentIngested, lambda e: calls.append("h2"))
        bus.publish(make_document_ingested())

        assert calls == ["h1", "h2"]

    def test_handler_called_multiple_times_for_multiple_publishes(self) -> None:
        bus = InProcessEventBus()
        received: list[DomainEvent] = []

        bus.subscribe(DocumentIngested, lambda e: received.append(e))
        bus.publish(make_document_ingested())
        bus.publish(make_document_ingested())

        assert len(received) == 2

    def test_multiple_event_types_independent(self) -> None:
        bus = InProcessEventBus()
        doc_received: list[DomainEvent] = []
        find_received: list[DomainEvent] = []

        bus.subscribe(DocumentIngested, lambda e: doc_received.append(e))
        bus.subscribe(FindingGenerated, lambda e: find_received.append(e))

        bus.publish(make_document_ingested())
        bus.publish(make_finding_generated())

        assert len(doc_received) == 1
        assert len(find_received) == 1

    def test_publish_with_no_subscribers_is_noop(self) -> None:
        bus = InProcessEventBus()
        bus.publish(make_document_ingested())  # should not raise

    def test_handler_receives_exact_event_instance(self) -> None:
        bus = InProcessEventBus()
        received: list[DomainEvent] = []

        bus.subscribe(DocumentIngested, lambda e: received.append(e))
        event = make_document_ingested()
        bus.publish(event)

        assert received[0] is event


# ---------------------------------------------------------------------------
# InProcessEventBus — deduplication of subscriptions
# ---------------------------------------------------------------------------


class TestInProcessEventBusDuplicateSubscriptions:
    def test_registering_same_handler_twice_is_noop(self) -> None:
        bus = InProcessEventBus()
        calls: list[int] = []
        handler = lambda e: calls.append(1)  # noqa: E731

        bus.subscribe(DocumentIngested, handler)
        bus.subscribe(DocumentIngested, handler)

        assert bus.subscriber_count(DocumentIngested) == 1
        bus.publish(make_document_ingested())
        assert calls == [1]

    def test_two_different_handlers_both_registered(self) -> None:
        bus = InProcessEventBus()
        h1 = lambda e: None  # noqa: E731
        h2 = lambda e: None  # noqa: E731

        bus.subscribe(DocumentIngested, h1)
        bus.subscribe(DocumentIngested, h2)

        assert bus.subscriber_count(DocumentIngested) == 2


# ---------------------------------------------------------------------------
# InProcessEventBus — unsubscribe
# ---------------------------------------------------------------------------


class TestInProcessEventBusUnsubscribe:
    def test_unsubscribed_handler_not_called(self) -> None:
        bus = InProcessEventBus()
        calls: list[int] = []
        handler = lambda e: calls.append(1)  # noqa: E731

        bus.subscribe(DocumentIngested, handler)
        bus.unsubscribe(DocumentIngested, handler)
        bus.publish(make_document_ingested())

        assert calls == []

    def test_unsubscribe_not_registered_is_noop(self) -> None:
        bus = InProcessEventBus()
        bus.unsubscribe(DocumentIngested, lambda e: None)  # should not raise

    def test_unsubscribe_only_removes_matching_handler(self) -> None:
        bus = InProcessEventBus()
        h1_calls: list[int] = []
        h2_calls: list[int] = []

        h1 = lambda e: h1_calls.append(1)  # noqa: E731
        h2 = lambda e: h2_calls.append(1)  # noqa: E731

        bus.subscribe(DocumentIngested, h1)
        bus.subscribe(DocumentIngested, h2)
        bus.unsubscribe(DocumentIngested, h1)
        bus.publish(make_document_ingested())

        assert h1_calls == []
        assert h2_calls == [1]


# ---------------------------------------------------------------------------
# InProcessEventBus — subscriber_count
# ---------------------------------------------------------------------------


class TestInProcessEventBusSubscriberCount:
    def test_zero_for_no_subscribers(self) -> None:
        bus = InProcessEventBus()
        assert bus.subscriber_count(DocumentIngested) == 0

    def test_increments_on_subscribe(self) -> None:
        bus = InProcessEventBus()
        bus.subscribe(DocumentIngested, lambda e: None)
        assert bus.subscriber_count(DocumentIngested) == 1
        bus.subscribe(DocumentIngested, lambda e: None)
        assert bus.subscriber_count(DocumentIngested) == 2

    def test_decrements_on_unsubscribe(self) -> None:
        bus = InProcessEventBus()
        h = lambda e: None  # noqa: E731
        bus.subscribe(DocumentIngested, h)
        bus.unsubscribe(DocumentIngested, h)
        assert bus.subscriber_count(DocumentIngested) == 0

    def test_different_types_counted_independently(self) -> None:
        bus = InProcessEventBus()
        bus.subscribe(DocumentIngested, lambda e: None)
        assert bus.subscriber_count(DocumentIngested) == 1
        assert bus.subscriber_count(FindingGenerated) == 0


# ---------------------------------------------------------------------------
# InProcessEventBus — handler error propagation
# ---------------------------------------------------------------------------


class TestInProcessEventBusErrorHandling:
    def test_handler_exception_propagates_to_publisher(self) -> None:
        bus = InProcessEventBus()

        def failing_handler(event: DomainEvent) -> None:
            raise ValueError("handler failed")

        bus.subscribe(DocumentIngested, failing_handler)
        with pytest.raises(ValueError, match="handler failed"):
            bus.publish(make_document_ingested())

    def test_subsequent_handlers_not_called_after_error(self) -> None:
        bus = InProcessEventBus()
        second_called: list[bool] = []

        bus.subscribe(
            DocumentIngested, lambda e: (_ for _ in ()).throw(RuntimeError("first fails"))
        )
        bus.subscribe(DocumentIngested, lambda e: second_called.append(True))

        with pytest.raises(RuntimeError):
            bus.publish(make_document_ingested())

        assert second_called == []


# ---------------------------------------------------------------------------
# InProcessEventBus — clear
# ---------------------------------------------------------------------------


class TestInProcessEventBusClear:
    def test_clear_removes_all_handlers(self) -> None:
        bus = InProcessEventBus()
        bus.subscribe(DocumentIngested, lambda e: None)
        bus.subscribe(FindingGenerated, lambda e: None)
        bus.clear()
        assert bus.subscriber_count(DocumentIngested) == 0
        assert bus.subscriber_count(FindingGenerated) == 0

    def test_publish_after_clear_is_noop(self) -> None:
        bus = InProcessEventBus()
        calls: list[int] = []
        bus.subscribe(DocumentIngested, lambda e: calls.append(1))
        bus.clear()
        bus.publish(make_document_ingested())
        assert calls == []
