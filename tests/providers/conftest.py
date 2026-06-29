"""
Provider conformance test configuration.

Provider conformance tests are marked with `pytest.mark.providers`.
Each conformance test module receives the provider under test through a fixture.

To add a new provider conformance test:
  1. Add a fixture here that instantiates the concrete provider
  2. Create tests/providers/test_<provider>_conformance.py
  3. Parametrize with all registered implementations if multiple exist

Provider fixtures are added here as concrete implementations are built (Sprint 2+).
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _providers_marker(request: pytest.FixtureRequest) -> None:
    """Auto-apply the 'providers' marker to all tests under tests/providers/."""
    request.node.add_marker(pytest.mark.providers)
