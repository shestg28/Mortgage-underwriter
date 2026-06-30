"""Unit tests for mil.identity.provider — IdP integration and token validation."""

from __future__ import annotations

import base64
import json
import time
from uuid import UUID, uuid4

import pytest

from mil.identity.provider import (
    DevIdentityProvider,
    IdentityProvider,
    TokenClaims,
    populate_authenticated_user,
)
from mil.kernel.errors import AuthenticationError
from mil.kernel.security import AuthenticatedUser, Role
from mil.kernel.types import TenantId, UserId

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_token(payload: dict[str, object]) -> str:
    """Encode a dict as a dev token."""
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"dev.{encoded}"


def _default_payload(tenant_id: str | None = None) -> dict[str, object]:
    tid = tenant_id or str(uuid4())
    return {
        "sub": "dev-user-001",
        "tid": tid,
        "roles": ["VERIFICATION_OFFICER"],
        "email": "dev@example.com",
        "display_name": "Dev User",
    }


# ---------------------------------------------------------------------------
# IdentityProvider abstract interface
# ---------------------------------------------------------------------------


class TestIdentityProviderInterface:
    def test_is_abstract(self) -> None:
        assert IdentityProvider.__abstractmethods__ != set()

    def test_validate_token_is_abstract(self) -> None:
        assert "validate_token" in IdentityProvider.__abstractmethods__

    def test_dev_provider_is_concrete_subclass(self) -> None:
        provider = DevIdentityProvider()
        assert isinstance(provider, IdentityProvider)


# ---------------------------------------------------------------------------
# TokenClaims
# ---------------------------------------------------------------------------


class TestTokenClaims:
    def test_minimal_construction(self) -> None:
        tid = TenantId(uuid4())
        claims = TokenClaims(subject="sub-001", tenant_id=tid)
        assert claims.subject == "sub-001"
        assert claims.tenant_id == tid
        assert claims.roles == frozenset()
        assert claims.email == ""
        assert claims.display_name == ""
        assert claims.issued_at is None
        assert claims.expires_at is None

    def test_full_construction(self) -> None:
        from datetime import UTC, datetime

        tid = TenantId(uuid4())
        now = datetime.now(UTC)
        claims = TokenClaims(
            subject="sub-002",
            tenant_id=tid,
            roles=frozenset({Role.UNDERWRITER}),
            email="user@bank.com",
            display_name="Underwriter One",
            issued_at=now,
            expires_at=now,
        )
        assert claims.roles == frozenset({Role.UNDERWRITER})
        assert claims.email == "user@bank.com"

    def test_is_immutable(self) -> None:
        from dataclasses import FrozenInstanceError

        tid = TenantId(uuid4())
        claims = TokenClaims(subject="s", tenant_id=tid)
        with pytest.raises(FrozenInstanceError):
            claims.subject = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DevIdentityProvider — valid tokens
# ---------------------------------------------------------------------------


class TestDevIdentityProviderValid:
    def setup_method(self) -> None:
        self.provider = DevIdentityProvider()

    def test_returns_token_claims(self) -> None:
        token = _make_token(_default_payload())
        claims = self.provider.validate_token(token)
        assert isinstance(claims, TokenClaims)

    def test_subject_extracted(self) -> None:
        token = _make_token(_default_payload())
        claims = self.provider.validate_token(token)
        assert claims.subject == "dev-user-001"

    def test_tenant_id_parsed(self) -> None:
        tid = str(uuid4())
        token = _make_token(_default_payload(tenant_id=tid))
        claims = self.provider.validate_token(token)
        assert claims.tenant_id == TenantId(UUID(tid))

    def test_roles_extracted(self) -> None:
        token = _make_token(_default_payload())
        claims = self.provider.validate_token(token)
        assert Role.VERIFICATION_OFFICER in claims.roles

    def test_email_extracted(self) -> None:
        token = _make_token(_default_payload())
        claims = self.provider.validate_token(token)
        assert claims.email == "dev@example.com"

    def test_display_name_extracted(self) -> None:
        token = _make_token(_default_payload())
        claims = self.provider.validate_token(token)
        assert claims.display_name == "Dev User"

    def test_empty_roles_default(self) -> None:
        payload = _default_payload()
        del payload["roles"]
        token = _make_token(payload)
        claims = self.provider.validate_token(token)
        assert claims.roles == frozenset()

    def test_multiple_roles(self) -> None:
        payload = _default_payload()
        payload["roles"] = [Role.VERIFICATION_OFFICER, Role.CREDIT_ANALYST]
        token = _make_token(payload)
        claims = self.provider.validate_token(token)
        assert Role.VERIFICATION_OFFICER in claims.roles
        assert Role.CREDIT_ANALYST in claims.roles

    def test_iat_and_exp_parsed(self) -> None:
        now = int(time.time())
        future = now + 3600
        payload = {**_default_payload(), "iat": now, "exp": future}
        token = _make_token(payload)
        claims = self.provider.validate_token(token)
        assert claims.issued_at is not None
        assert claims.expires_at is not None

    def test_missing_optional_fields_use_defaults(self) -> None:
        payload = {"sub": "sub-x", "tid": str(uuid4())}
        token = _make_token(payload)
        claims = self.provider.validate_token(token)
        assert claims.email == ""
        assert claims.display_name == ""

    def test_token_with_padding_tolerance(self) -> None:
        """Base64 padding (%3) is handled gracefully."""
        payload = _default_payload()
        # Construct a token with unpadded base64.
        raw = json.dumps(payload).encode()
        b64 = base64.b64encode(raw).decode().rstrip("=")
        token = f"dev.{b64}"
        claims = self.provider.validate_token(token)
        assert claims.subject == "dev-user-001"


# ---------------------------------------------------------------------------
# DevIdentityProvider — invalid tokens
# ---------------------------------------------------------------------------


class TestDevIdentityProviderInvalid:
    def setup_method(self) -> None:
        self.provider = DevIdentityProvider()

    def test_missing_dev_prefix_raises(self) -> None:
        with pytest.raises(AuthenticationError, match=r"prefixed with 'dev\.'"):
            self.provider.validate_token("notadevtoken")

    def test_invalid_base64_raises(self) -> None:
        with pytest.raises(AuthenticationError):
            self.provider.validate_token("dev.!!!notbase64!!!")

    def test_missing_sub_raises(self) -> None:
        payload = _default_payload()
        del payload["sub"]
        with pytest.raises(AuthenticationError, match="'sub'"):
            self.provider.validate_token(_make_token(payload))

    def test_empty_sub_raises(self) -> None:
        payload = {**_default_payload(), "sub": ""}
        with pytest.raises(AuthenticationError, match="'sub'"):
            self.provider.validate_token(_make_token(payload))

    def test_missing_tid_raises(self) -> None:
        payload = _default_payload()
        del payload["tid"]
        with pytest.raises(AuthenticationError, match="'tid'"):
            self.provider.validate_token(_make_token(payload))

    def test_invalid_tid_uuid_raises(self) -> None:
        payload = {**_default_payload(), "tid": "not-a-uuid"}
        with pytest.raises(AuthenticationError, match="not a valid UUID"):
            self.provider.validate_token(_make_token(payload))

    def test_roles_not_list_raises(self) -> None:
        payload = {**_default_payload(), "roles": "VERIFICATION_OFFICER"}
        with pytest.raises(AuthenticationError, match="'roles' must be a list"):
            self.provider.validate_token(_make_token(payload))

    def test_expired_token_raises(self) -> None:
        payload = {**_default_payload(), "exp": int(time.time()) - 1}
        with pytest.raises(AuthenticationError, match="expired"):
            self.provider.validate_token(_make_token(payload))

    def test_non_json_payload_raises(self) -> None:
        raw_b64 = base64.b64encode(b"this is not json").decode()
        with pytest.raises(AuthenticationError):
            self.provider.validate_token(f"dev.{raw_b64}")


# ---------------------------------------------------------------------------
# populate_authenticated_user
# ---------------------------------------------------------------------------


class TestPopulateAuthenticatedUser:
    def _make_claims(self, roles: list[str] | None = None) -> TokenClaims:
        role_set = roles if roles is not None else [Role.VERIFICATION_OFFICER]
        return TokenClaims(
            subject="ext-sub-001",
            tenant_id=TenantId(uuid4()),
            roles=frozenset(role_set),
            email="user@bank.com",
            display_name="Test User",
        )

    def test_returns_authenticated_user(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims()
        user = populate_authenticated_user(claims, user_id=user_id)
        assert isinstance(user, AuthenticatedUser)

    def test_user_id_is_mil_internal(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims()
        user = populate_authenticated_user(claims, user_id=user_id)
        assert user.user_id == user_id
        # Internal user_id != external subject
        assert str(user.user_id) != claims.subject

    def test_tenant_id_propagated(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims()
        user = populate_authenticated_user(claims, user_id=user_id)
        assert user.tenant_id == claims.tenant_id

    def test_roles_propagated(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims(roles=[Role.UNDERWRITER, Role.CREDIT_ANALYST])
        user = populate_authenticated_user(claims, user_id=user_id)
        assert Role.UNDERWRITER in user.roles
        assert Role.CREDIT_ANALYST in user.roles

    def test_email_propagated(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims()
        user = populate_authenticated_user(claims, user_id=user_id)
        assert user.email == "user@bank.com"

    def test_display_name_propagated(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims()
        user = populate_authenticated_user(claims, user_id=user_id)
        assert user.display_name == "Test User"

    def test_result_is_immutable(self) -> None:
        from dataclasses import FrozenInstanceError

        user_id = UserId(uuid4())
        claims = self._make_claims()
        user = populate_authenticated_user(claims, user_id=user_id)
        with pytest.raises(FrozenInstanceError):
            user.email = "hacked@evil.com"  # type: ignore[misc]

    def test_empty_roles_produces_empty_frozenset(self) -> None:
        user_id = UserId(uuid4())
        claims = self._make_claims(roles=[])
        user = populate_authenticated_user(claims, user_id=user_id)
        assert user.roles == frozenset()
