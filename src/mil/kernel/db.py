"""
SQLAlchemy declarative base and async engine factory.

This module is the single source of truth for the ORM base class. Every model
in every bounded context inherits from `Base`. Alembic's env.py imports
`Base.metadata` so that autogenerate can discover all registered tables.

To register a model with Alembic autogenerate, import it in the bounded context's
`models.py` and ensure that models.py is imported in migrations/env.py under the
"Import bounded context models" block.

The async engine and session factories are configured from `mil.kernel.config`
(implemented in T009). Only the Base and synchronous migration engine are
required in Sprint 1.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for database constraints ensures Alembic can reliably
# generate ALTER TABLE statements when constraints are added or removed.
_NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Shared declarative base for all MIL ORM models.

    All bounded context models inherit from this class. The metadata object
    carries the constraint naming convention required for reliable Alembic
    migrations across all supported PostgreSQL schemas.
    """

    metadata = MetaData(naming_convention=_NAMING_CONVENTION)
