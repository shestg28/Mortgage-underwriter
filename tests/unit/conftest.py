"""
Unit test configuration.

Unit tests must not require any external infrastructure. If a test needs a
database, message broker, or object storage, it belongs in tests/integration/.

Fixtures here provide lightweight in-process stubs for bounded context
dependencies. Concrete stub implementations are added here as bounded contexts
are implemented (Sprint 2+).
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _unit_marker(request: pytest.FixtureRequest) -> None:
    """Auto-apply the 'unit' marker to all tests under tests/unit/."""
    request.node.add_marker(pytest.mark.unit)
