"""
Relay abstraction for the Transactional Outbox (ADR-007).

The relay is the component that, *after commit*, reads committed-but-unpublished
outbox rows and publishes them to the broker (``EventBus``), marking each row
published once the broker accepts it. This establishes commit-before-publish
and at-least-once delivery.

This sprint persists only. **No broker publishing is implemented.** This module
provides:

- ``Relay`` — the abstract, replaceable interface.
- ``NoOpRelay`` — an inert default that publishes nothing and leaves outbox
  rows PENDING. It satisfies the interface so the wiring seam exists, without
  introducing a broker dependency. A broker-backed relay (e.g. Redis Streams,
  AMQP) is registered in production by substituting an implementation of
  ``Relay`` — no change to producing code.

Dependency rule: imports only from ``mil.outbox`` and the Python standard
library.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Relay(ABC):
    """
    Abstract, replaceable outbox relay.

    A concrete relay drains committed outbox rows and publishes them to the
    broker after commit. The interface is intentionally minimal so any
    broker-backed implementation can be substituted without touching the
    producing contexts (ADR-007).
    """

    @abstractmethod
    def relay_pending(self, *, limit: int = 100) -> int:
        """
        Publish up to ``limit`` committed, unpublished outbox events.

        Returns the number of events published. Implementations MUST only mark
        a row published after the broker has accepted it, preserving
        at-least-once delivery (ADR-007): a crash before marking results in
        redelivery, which downstream consumers absorb via idempotency (ADR-008).
        """


class NoOpRelay(Relay):
    """
    Inert relay used in US2 Sprint 1.

    Publishes nothing and marks nothing published; outbox rows accumulate in
    PENDING state awaiting a real, broker-backed relay. This keeps the sprint
    honest about its scope ("persist only") while providing the replaceable
    seam the architecture requires.
    """

    def relay_pending(self, *, limit: int = 100) -> int:
        return 0
