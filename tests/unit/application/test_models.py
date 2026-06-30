"""Unit tests for mil.application.models — PartyType enumeration."""

from __future__ import annotations

import pytest

from mil.application.models import PartyType

# ---------------------------------------------------------------------------
# PartyType
# ---------------------------------------------------------------------------


class TestPartyType:
    def test_all_expected_members_exist(self) -> None:
        expected = {"APPLICANT", "CO_APPLICANT", "GUARANTOR", "CORPORATE_ENTITY"}
        actual = {pt.value for pt in PartyType}
        assert actual == expected

    def test_members_are_strings(self) -> None:
        for pt in PartyType:
            assert isinstance(pt, str), f"{pt} should be a str (StrEnum)"

    def test_lookup_by_value(self) -> None:
        assert PartyType("APPLICANT") is PartyType.APPLICANT
        assert PartyType("GUARANTOR") is PartyType.GUARANTOR

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            PartyType("INVALID_TYPE")

    def test_values_match_names(self) -> None:
        for pt in PartyType:
            assert pt.value == pt.name

    def test_is_str_subtype(self) -> None:
        assert issubclass(PartyType, str)

    def test_equality_with_plain_string(self) -> None:
        assert PartyType.APPLICANT == "APPLICANT"
        assert PartyType.CO_APPLICANT == "CO_APPLICANT"
