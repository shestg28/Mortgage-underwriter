"""
ORM models for the Application & Party bounded context.

This module will contain the Application and Party ORM models (T034).
Currently it defines the PartyType enumeration, which is a domain concept
of the Party entity and belongs to this bounded context.

Schema: all tables live in the ``core`` PostgreSQL schema.

Dependency rule: imports only from ``mil.kernel.db`` and the Python
standard library.  No bounded context may import from another bounded
context.
"""

from __future__ import annotations

import enum

# ---------------------------------------------------------------------------
# Enumeration: PartyType
# ---------------------------------------------------------------------------


class PartyType(enum.StrEnum):
    """
    The role a party plays within a mortgage application.

    Stored as a VARCHAR string in the database (``core.parties.party_type``)
    rather than a native PostgreSQL ENUM to allow adding values without a
    DDL migration.

    Values match the approved data model enumeration in ``data-model.md``.
    """

    APPLICANT = "APPLICANT"
    CO_APPLICANT = "CO_APPLICANT"
    GUARANTOR = "GUARANTOR"
    CORPORATE_ENTITY = "CORPORATE_ENTITY"


# T034 will add Application and Party ORM models to this file.
