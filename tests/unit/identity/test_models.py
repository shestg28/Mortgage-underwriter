"""Unit tests for mil.identity.models — User, Role, and RoleAssignment ORM models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from mil.identity.models import Role, RoleAssignment, User

# ---------------------------------------------------------------------------
# User ORM model
# ---------------------------------------------------------------------------


class TestUserModel:
    def _make_user(self) -> User:
        return User(
            id=uuid4(),
            tenant_id=uuid4(),
            external_identity_id="external-sub-001",
            email_hash="abc" * 10 + "ab",
            display_name="Alice",
            is_active=True,
            created_at=datetime.now(UTC),
        )

    def test_tablename(self) -> None:
        assert User.__tablename__ == "users"

    def test_schema(self) -> None:
        assert User.__table_args__["schema"] == "core"

    def test_fields_accessible(self) -> None:
        user = self._make_user()
        assert user.display_name == "Alice"
        assert user.is_active is True
        assert isinstance(user.tenant_id, UUID)

    def test_is_active_explicit_false(self) -> None:
        user = User(
            tenant_id=uuid4(),
            external_identity_id="sub-002",
            email_hash="x" * 32,
            display_name="Bob",
            is_active=False,
        )
        assert user.is_active is False

    def test_repr_contains_key_info(self) -> None:
        user = self._make_user()
        r = repr(user)
        assert "User" in r
        assert "tenant" in r

    def test_external_identity_id_stored(self) -> None:
        user = self._make_user()
        assert user.external_identity_id == "external-sub-001"

    def test_created_at_timezone_aware(self) -> None:
        user = self._make_user()
        assert user.created_at.tzinfo is not None


# ---------------------------------------------------------------------------
# Role ORM model
# ---------------------------------------------------------------------------


class TestRoleModel:
    def _make_role(self, name: str = "VERIFICATION_OFFICER") -> Role:
        return Role(
            id=uuid4(),
            tenant_id=uuid4(),
            name=name,
            description="A verification officer role",
            created_at=datetime.now(UTC),
        )

    def test_tablename(self) -> None:
        assert Role.__tablename__ == "roles"

    def test_schema(self) -> None:
        assert Role.__table_args__["schema"] == "core"

    def test_name_stored(self) -> None:
        role = self._make_role()
        assert role.name == "VERIFICATION_OFFICER"

    def test_description_optional(self) -> None:
        role = Role(id=uuid4(), tenant_id=uuid4(), name="ADMIN")
        assert role.description is None

    def test_repr_contains_name(self) -> None:
        role = self._make_role()
        assert "VERIFICATION_OFFICER" in repr(role)


# ---------------------------------------------------------------------------
# RoleAssignment ORM model
# ---------------------------------------------------------------------------


class TestRoleAssignmentModel:
    def _make_assignment(
        self,
        *,
        revoked_at: datetime | None = None,
    ) -> RoleAssignment:
        return RoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            assigned_by=uuid4(),
            assigned_at=datetime.now(UTC),
            revoked_at=revoked_at,
        )

    def test_tablename(self) -> None:
        assert RoleAssignment.__tablename__ == "role_assignments"

    def test_schema(self) -> None:
        assert RoleAssignment.__table_args__["schema"] == "core"

    def test_is_active_when_not_revoked(self) -> None:
        assignment = self._make_assignment()
        assert assignment.is_active is True

    def test_is_inactive_when_revoked(self) -> None:
        assignment = self._make_assignment(revoked_at=datetime.now(UTC))
        assert assignment.is_active is False

    def test_revoked_at_defaults_to_none(self) -> None:
        assignment = RoleAssignment(
            user_id=uuid4(),
            role_id=uuid4(),
            assigned_by=uuid4(),
            assigned_at=datetime.now(UTC),
        )
        assert assignment.revoked_at is None

    def test_repr_shows_active_status(self) -> None:
        assignment = self._make_assignment()
        r = repr(assignment)
        assert "RoleAssignment" in r
        assert "active=True" in r

    def test_assigned_by_is_separate_from_user_id(self) -> None:
        user_id = uuid4()
        assigner_id = uuid4()
        assignment = self._make_assignment()
        assignment.user_id = user_id
        assignment.assigned_by = assigner_id
        assert assignment.user_id != assignment.assigned_by
