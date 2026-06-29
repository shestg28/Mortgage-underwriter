"""
Contract test configuration.

Contract tests are marked with `pytest.mark.contract` and require a running
MIL API instance. The API base URL is read from the `api_base_url` fixture
defined in tests/conftest.py (configurable via MIL_API_BASE_URL env var).

Contracts under test:
  specs/001-mil-platform-spec/contracts/applications.yaml
  specs/001-mil-platform-spec/contracts/documents.yaml
  specs/001-mil-platform-spec/contracts/evidence.yaml
  specs/001-mil-platform-spec/contracts/findings.yaml
  specs/001-mil-platform-spec/contracts/copilot.yaml
  specs/001-mil-platform-spec/contracts/audit.yaml
  specs/001-mil-platform-spec/contracts/operational.yaml
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _contract_marker(request: pytest.FixtureRequest) -> None:
    """Auto-apply the 'contract' marker to all tests under tests/contract/."""
    request.node.add_marker(pytest.mark.contract)
