"""
Integration test configuration.

Integration tests run against real infrastructure managed by testcontainers.
Each test session starts a PostgreSQL container, applies migrations, and tears
it down on completion. Redis and MinIO containers are added here as their
respective bounded contexts are implemented (Sprint 2+).

PREREQUISITES
-------------
  - Docker must be running
  - Package must be installed: make install-dev
  - Run: pytest tests/integration -m integration

ISOLATION
---------
The database fixture uses session scope — one container and one schema per
pytest session. Tests that modify data must restore state in teardown or use
transactions that are rolled back. Factory fixtures are added per bounded
context as implementation progresses.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _integration_marker(request: pytest.FixtureRequest) -> None:
    """Auto-apply the 'integration' marker to all tests under tests/integration/."""
    request.node.add_marker(pytest.mark.integration)


# ---------------------------------------------------------------------------
# Infrastructure fixtures (implemented when Sprint 2+ bounded contexts exist)
# ---------------------------------------------------------------------------
#
# The following fixtures will be added here as bounded contexts are implemented:
#
# @pytest.fixture(scope="session")
# def postgres_container():
#     from testcontainers.postgres import PostgresContainer
#     with PostgresContainer("postgres:16-alpine") as pg:
#         yield pg
#
# @pytest.fixture(scope="session")
# def db_engine(postgres_container):
#     from sqlalchemy import create_engine
#     from mil.kernel.db import Base
#     # import all model modules here to register tables
#     engine = create_engine(postgres_container.get_connection_url())
#     Base.metadata.create_all(engine)
#     yield engine
#     Base.metadata.drop_all(engine)
#
# @pytest.fixture
# async def db_session(db_engine):
#     from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
#     ...
