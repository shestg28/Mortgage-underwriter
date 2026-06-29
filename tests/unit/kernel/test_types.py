"""Unit tests for mil.kernel.types — typed identifiers and value objects."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from mil.kernel.types import (
    ApplicationId,
    AuditEventId,
    Confidence,
    DocumentId,
    EvidenceItemId,
    FindingId,
    Money,
    PartyId,
    PolicyPackId,
    PolicyVersion,
    TenantId,
    UserId,
    VerificationId,
    WorkflowRunId,
    new_application_id,
    new_audit_event_id,
    new_document_id,
    new_evidence_item_id,
    new_finding_id,
    new_party_id,
    new_policy_pack_id,
    new_tenant_id,
    new_user_id,
    new_verification_id,
    new_workflow_run_id,
)

# ---------------------------------------------------------------------------
# Typed identifiers — factory functions
# ---------------------------------------------------------------------------


class TestTypedIdentifierFactories:
    def test_new_application_id_returns_uuid(self) -> None:
        app_id = new_application_id()
        assert isinstance(app_id, UUID)

    def test_factory_functions_return_unique_values(self) -> None:
        assert new_application_id() != new_application_id()
        assert new_evidence_item_id() != new_evidence_item_id()
        assert new_finding_id() != new_finding_id()

    def test_all_factory_functions_return_uuids(self) -> None:
        factories_and_types = [
            (new_application_id, ApplicationId),
            (new_party_id, PartyId),
            (new_document_id, DocumentId),
            (new_evidence_item_id, EvidenceItemId),
            (new_finding_id, FindingId),
            (new_verification_id, VerificationId),
            (new_policy_pack_id, PolicyPackId),
            (new_audit_event_id, AuditEventId),
            (new_workflow_run_id, WorkflowRunId),
            (new_tenant_id, TenantId),
            (new_user_id, UserId),
        ]
        for factory, _ in factories_and_types:
            result = factory()
            assert isinstance(result, UUID), f"{factory.__name__} should return a UUID"

    def test_typed_ids_constructed_from_uuid(self) -> None:
        raw = uuid4()
        app_id = ApplicationId(raw)
        assert app_id == raw

    def test_typed_ids_are_not_interchangeable_at_runtime(self) -> None:
        raw = uuid4()
        app_id = ApplicationId(raw)
        evidence_id = EvidenceItemId(raw)
        # Same underlying value but different logical types.
        # At runtime they are equal as UUIDs; mypy prevents confusion at
        # type-check time.
        assert app_id == evidence_id


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------


class TestMoney:
    def test_create_valid_money(self) -> None:
        m = Money(amount=Decimal("500.00"), currency="GBP")
        assert m.amount == Decimal("500.00")
        assert m.currency == "GBP"

    def test_money_of_classmethod_from_string(self) -> None:
        m = Money.of("1234.56", "USD")
        assert m.amount == Decimal("1234.56")
        assert m.currency == "USD"

    def test_money_of_classmethod_upcases_currency(self) -> None:
        m = Money.of("100", "gbp")
        assert m.currency == "GBP"

    def test_money_of_from_integer(self) -> None:
        m = Money.of(1000, "AUD")
        assert m.amount == Decimal("1000")

    def test_money_of_from_decimal(self) -> None:
        m = Money.of(Decimal("99.99"), "EUR")
        assert m.amount == Decimal("99.99")

    def test_money_zero_amount_allowed(self) -> None:
        m = Money(amount=Decimal("0"), currency="GBP")
        assert m.amount == Decimal("0")

    def test_money_negative_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(amount=Decimal("-1"), currency="GBP")

    def test_money_invalid_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="ISO 4217"):
            Money(amount=Decimal("100"), currency="INVALID")

    def test_money_empty_currency_raises(self) -> None:
        with pytest.raises(ValueError):
            Money(amount=Decimal("100"), currency="")

    def test_money_non_decimal_amount_raises(self) -> None:
        with pytest.raises(TypeError, match="Decimal"):
            Money(amount=100.0, currency="GBP")  # type: ignore[arg-type]

    def test_money_of_invalid_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid monetary amount"):
            Money.of("not-a-number", "GBP")

    def test_money_is_immutable(self) -> None:
        m = Money(amount=Decimal("100"), currency="GBP")
        with pytest.raises(FrozenInstanceError):
            m.amount = Decimal("200")  # type: ignore[misc]

    def test_money_str_representation(self) -> None:
        m = Money(amount=Decimal("1500.00"), currency="GBP")
        assert "GBP" in str(m)
        assert "1500.00" in str(m)

    def test_money_equality(self) -> None:
        a = Money(amount=Decimal("100"), currency="USD")
        b = Money(amount=Decimal("100"), currency="USD")
        assert a == b

    def test_money_inequality_different_currency(self) -> None:
        a = Money(amount=Decimal("100"), currency="USD")
        b = Money(amount=Decimal("100"), currency="GBP")
        assert a != b


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


class TestConfidence:
    def test_create_high_confidence(self) -> None:
        c = Confidence(score=0.95)
        assert c.score == 0.95
        assert c.label == "HIGH"

    def test_create_medium_confidence(self) -> None:
        c = Confidence(score=0.72)
        assert c.label == "MEDIUM"

    def test_create_low_confidence(self) -> None:
        c = Confidence(score=0.40)
        assert c.label == "LOW"

    def test_boundary_high_threshold(self) -> None:
        assert Confidence(score=0.85).label == "HIGH"
        assert Confidence(score=0.849).label == "MEDIUM"

    def test_boundary_medium_threshold(self) -> None:
        assert Confidence(score=0.60).label == "MEDIUM"
        assert Confidence(score=0.599).label == "LOW"

    def test_zero_score_is_valid(self) -> None:
        c = Confidence(score=0.0)
        assert c.score == 0.0
        assert c.label == "LOW"

    def test_full_score_is_valid(self) -> None:
        c = Confidence(score=1.0)
        assert c.score == 1.0
        assert c.label == "HIGH"

    def test_negative_score_raises(self) -> None:
        with pytest.raises(ValueError, match=r"\[0.0, 1.0\]"):
            Confidence(score=-0.1)

    def test_score_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match=r"\[0.0, 1.0\]"):
            Confidence(score=1.01)

    def test_confidence_is_immutable(self) -> None:
        c = Confidence(score=0.9)
        with pytest.raises(FrozenInstanceError):
            c.score = 0.5  # type: ignore[misc]

    def test_confidence_str_includes_label(self) -> None:
        s = str(Confidence(score=0.9))
        assert "HIGH" in s

    def test_confidence_equality(self) -> None:
        assert Confidence(score=0.8) == Confidence(score=0.8)


# ---------------------------------------------------------------------------
# PolicyVersion
# ---------------------------------------------------------------------------


class TestPolicyVersion:
    def test_create_version(self) -> None:
        v = PolicyVersion(major=1, minor=2, patch=3)
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_str_format(self) -> None:
        assert str(PolicyVersion(major=2, minor=0, patch=1)) == "2.0.1"

    def test_parse_valid_string(self) -> None:
        v = PolicyVersion.parse("1.4.7")
        assert v.major == 1
        assert v.minor == 4
        assert v.patch == 7

    def test_parse_roundtrip(self) -> None:
        original = PolicyVersion(major=3, minor=1, patch=0)
        parsed = PolicyVersion.parse(str(original))
        assert parsed == original

    def test_parse_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match=r"MAJOR\.MINOR\.PATCH"):
            PolicyVersion.parse("1.2")

    def test_parse_non_integer_raises(self) -> None:
        with pytest.raises(ValueError):
            PolicyVersion.parse("1.2.x")

    def test_negative_component_raises(self) -> None:
        with pytest.raises(ValueError):
            PolicyVersion(major=-1, minor=0, patch=0)

    def test_zero_version_is_valid(self) -> None:
        v = PolicyVersion(major=0, minor=0, patch=0)
        assert str(v) == "0.0.0"

    def test_is_compatible_with_same_version(self) -> None:
        v = PolicyVersion(major=1, minor=2, patch=3)
        assert v.is_compatible_with(PolicyVersion(major=1, minor=2, patch=3))

    def test_is_compatible_with_older_patch(self) -> None:
        newer = PolicyVersion(major=1, minor=2, patch=3)
        older = PolicyVersion(major=1, minor=2, patch=1)
        assert newer.is_compatible_with(older)

    def test_not_compatible_with_different_major(self) -> None:
        v1 = PolicyVersion(major=1, minor=0, patch=0)
        v2 = PolicyVersion(major=2, minor=0, patch=0)
        assert not v1.is_compatible_with(v2)
        assert not v2.is_compatible_with(v1)

    def test_not_compatible_with_newer_minor(self) -> None:
        older = PolicyVersion(major=1, minor=1, patch=0)
        newer = PolicyVersion(major=1, minor=2, patch=0)
        assert not older.is_compatible_with(newer)

    def test_policy_version_is_immutable(self) -> None:
        v = PolicyVersion(major=1, minor=0, patch=0)
        with pytest.raises(FrozenInstanceError):
            v.major = 2  # type: ignore[misc]
