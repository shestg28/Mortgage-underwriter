"""
ORM models for the Identity & Access bounded context.

This module defines the SQLAlchemy models for ``core.users``,
``core.roles``, and ``core.role_assignments``.

Schema: all tables live in the ``core`` PostgreSQL schema.

Dependency rule: this module imports from ``mil.kernel.db`` and the
Python standard library only.  No bounded context may import from
another bounded context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mil.kernel.db import Base

# ---------------------------------------------------------------------------
# ORM Model: User
# ---------------------------------------------------------------------------


class User(Base):
    """
    Represents an authenticated platform user.

    ``external_identity_id`` is the ``sub`` claim from the external IdP
    token.  It is the stable, IdP-assigned identifier for the user.

    ``email_hash`` stores a hashed form of the email address to support
    lookup by email without storing PII in plaintext.  The hash is
    computed by the identity bounded context using SHA-256.

    PII is not stored in plaintext per Engineering Constitution Principle V
    (Security & Privacy by Design).
    """

    __tablename__ = "users"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    external_identity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    role_assignments: Mapped[list[RoleAssignment]] = relationship(
        "RoleAssignment",
        foreign_keys="RoleAssignment.user_id",
        back_populates="user",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tenant={self.tenant_id}>"


# ---------------------------------------------------------------------------
# ORM Model: Role
# ---------------------------------------------------------------------------


class Role(Base):
    """
    An RBAC role that can be assigned to users.

    Role names match the string constants in ``mil.kernel.security.Role``
    (e.g. ``"VERIFICATION_OFFICER"``, ``"UNDERWRITER"``).  The name is
    the stable identifier used throughout the platform; the ``id`` is an
    internal surrogate key.

    Roles are tenant-scoped — each tenant maintains its own role records
    even if the names match the platform defaults.
    """

    __tablename__ = "roles"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    role_assignments: Mapped[list[RoleAssignment]] = relationship(
        "RoleAssignment",
        back_populates="role",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Role name={self.name!r} tenant={self.tenant_id}>"


# ---------------------------------------------------------------------------
# ORM Model: RoleAssignment
# ---------------------------------------------------------------------------


class RoleAssignment(Base):
    """
    An assignment of a Role to a User, with optional revocation.

    An assignment is active when ``revoked_at`` is NULL.  Revocation uses
    a soft-delete (setting ``revoked_at``) rather than row deletion to
    preserve the audit history of who held which roles and when.

    Every assignment records the ``assigned_by`` user to satisfy the
    Engineering Constitution Principle VIII (Auditability) requirement
    that all significant platform actions be traceable.
    """

    __tablename__ = "role_assignments"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("core.users.id"),
        nullable=False,
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("core.roles.id"),
        nullable=False,
    )
    assigned_by: Mapped[UUID] = mapped_column(
        ForeignKey("core.users.id"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    # NULL = still active; non-NULL = revoked at this timestamp.
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="role_assignments",
    )
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="role_assignments",
    )

    @property
    def is_active(self) -> bool:
        """Return True if this assignment has not been revoked."""
        return self.revoked_at is None

    def __repr__(self) -> str:
        return f"<RoleAssignment user={self.user_id} role={self.role_id} active={self.is_active}>"
