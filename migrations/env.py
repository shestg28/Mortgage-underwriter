"""
Alembic migration environment.

This file is executed by Alembic for both offline migration generation
(alembic revision --autogenerate) and online migration execution (alembic upgrade).

DATABASE URL RESOLUTION
-----------------------
The synchronous database URL is resolved in this order:
  1. ALEMBIC_DATABASE_URL environment variable (explicit override)
  2. Constructed from POSTGRES_* environment variables

The URL must use a synchronous driver (psycopg2) even though the application
uses an async driver (asyncpg) at runtime. Alembic migrations always run
synchronously.

ADDING NEW MODELS FOR AUTOGENERATE
------------------------------------
When a new bounded context adds ORM models, import the models module here
under "Import bounded context models" so that Alembic can discover the tables
and include them in --autogenerate output.

Example:
    from mil.application import models as _application_models  # noqa: F401

The import is assigned to a variable prefixed with underscore to satisfy the
unused-import linter rule while ensuring the module is evaluated (which
registers the models in Base.metadata).
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Ensure the src/ directory is on the Python path so that `mil` is importable
# when running alembic directly (without the package installed in editable mode).
# If the package is installed (`pip install -e .`), this is redundant but harmless.
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

# ---------------------------------------------------------------------------
# Import the SQLAlchemy declarative base.
# Base.metadata is used by Alembic for --autogenerate table comparison.
# ---------------------------------------------------------------------------
# Sprint 3B — Application & Party + Audit
from mil.application import models as _application_models  # noqa: E402, F401
from mil.audit import models as _audit_models  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Import bounded context models so that their tables are registered in
# Base.metadata and visible to --autogenerate.
#
# Add one import per bounded context as models are implemented in Sprint 2+:
#
# from mil.document import models as _document_models
# from mil.evidence import models as _evidence_models
# from mil.policy import models as _policy_models
# from mil.finding import models as _finding_models
# from mil.review import models as _review_models
# from mil.operational import models as _operational_models
# from mil.integration import models as _integration_models
# from mil.orchestrator import models as _orchestrator_models
# ---------------------------------------------------------------------------
# Sprint 3A — Identity & Access
from mil.identity import models as _identity_models  # noqa: E402, F401
from mil.kernel.db import Base  # noqa: E402

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Alembic configuration
# ---------------------------------------------------------------------------

# Access to alembic.ini values (fileConfig also configures Python logging)
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _get_database_url() -> str:
    """
    Resolve the synchronous database URL for Alembic migrations.

    Precedence:
      1. ALEMBIC_DATABASE_URL — explicit full DSN override
      2. POSTGRES_* variables — constructed DSN from individual components
    """
    explicit = os.getenv("ALEMBIC_DATABASE_URL")
    if explicit:
        return explicit

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "mil")
    user = os.getenv("POSTGRES_USER", "mil")
    password = os.getenv("POSTGRES_PASSWORD", "changeme")

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.

    Offline mode generates SQL to stdout (or a file) without requiring a live
    database connection. Useful for reviewing migrations before applying them
    or for applying migrations via a DBA pipeline.

        alembic upgrade head --sql
    """
    url = _get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include schemas so that tables in non-public schemas (audit, evidence,
        # finding, review, oi) are correctly addressed in generated SQL.
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online mode against a live database connection.

        alembic upgrade head
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no connection pooling in migration runs
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
