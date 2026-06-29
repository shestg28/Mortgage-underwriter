"""
EventBus abstraction for the MIL Platform.

The ``EventBus`` interface is the platform-level coordination primitive for
domain event publication and subscription.  Bounded contexts publish events
via ``EventBus.publish``; the Intelligence Orchestrator and other interested
parties subscribe via ``EventBus.subscribe``.

The concrete backing implementation (in-process, Redis Pub/Sub, AMQP, etc.)
is registered in the dependency injection container at startup.  All bounded
context code resolves ``EventBus`` from the container — it has no dependency
on any concrete implementation.

This module provides:

- ``EventBus`` — abstract interface (ABC) for platform event dispatch.
- ``InProcessEventBus`` — synchronous, in-memory implementation for
  development and testing.  Handler errors are propagated immediately so
  bugs in subscribers surface during development.

Dependency rule: this module imports from ``mil.kernel.events`` and the
Python standard library only.  No bounded context code should be imported.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mil.kernel.events import DomainEvent

# ---------------------------------------------------------------------------
# Handler protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class EventHandler(Protocol):
    """
    Callable protocol for domain event handlers.

    Any callable that accepts a single ``DomainEvent`` argument and returns
    ``None`` satisfies this protocol.  Handlers SHOULD be idempotent because
    broker-backed implementations may deliver events more than once.
    """

    def __call__(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        ...


# ---------------------------------------------------------------------------
# Abstract EventBus interface
# ---------------------------------------------------------------------------


class EventBus(ABC):
    """
    Abstract interface for publishing and subscribing to domain events.

    All bounded context code depends on this interface.  The concrete
    implementation is resolved from the DI container at runtime.
    """

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event to all registered subscribers.

        The caller must not assume any ordering of handler invocations.
        Handler errors are implementation-defined: in-process raises
        immediately; broker-backed implementations typically re-queue.
        """

    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """
        Register a handler for a specific event type.

        Registering the same handler for the same event type more than once
        is a no-op: duplicate registrations are silently ignored.

        Args:
            event_type: The concrete ``DomainEvent`` subclass to subscribe to.
            handler:    A callable that accepts an instance of ``event_type``.
        """

    @abstractmethod
    def unsubscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """
        Remove a previously registered handler.

        Unsubscribing a handler that was never registered is a no-op.
        """

    @abstractmethod
    def subscriber_count(self, event_type: type[DomainEvent]) -> int:
        """Return the number of handlers registered for ``event_type``."""


# ---------------------------------------------------------------------------
# In-process implementation
# ---------------------------------------------------------------------------


class InProcessEventBus(EventBus):
    """
    Synchronous, in-memory ``EventBus`` implementation.

    Handlers are invoked synchronously in the order they were subscribed.
    Any exception raised by a handler propagates to the ``publish`` caller
    immediately, aborting remaining handlers for that event.  This strict
    behaviour surfaces bugs early in development and test environments.

    Thread-safety: not guaranteed.  This implementation is intended for
    single-threaded test suites and local development.  Production
    deployments should register a broker-backed implementation.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def publish(self, event: DomainEvent) -> None:
        # Snapshot the handler list before iterating so that a handler that
        # subscribes or unsubscribes during dispatch does not affect this call.
        handlers = list(self._handlers.get(type(event), []))
        for handler in handlers:
            handler(event)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h is not handler]

    def subscriber_count(self, event_type: type[DomainEvent]) -> int:
        return len(self._handlers.get(event_type, []))

    def clear(self) -> None:
        """Remove all registered handlers. Useful between test cases."""
        self._handlers.clear()
