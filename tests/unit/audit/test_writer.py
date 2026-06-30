"""Unit tests for mil.audit.writer — AuditWriter."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from mil.audit.models import AuditEvent
from mil.audit.writer import AuditWriter


def _make_writer() -> tuple[AuditWriter, MagicMock]:
    session = MagicMock()
    return AuditWriter(session), session


class TestAuditWriterRecord:
    def test_record_returns_audit_event(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert isinstance(event, AuditEvent)

    def test_record_adds_event_to_session(self) -> None:
        writer, session = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        session.add.assert_called_once_with(event)

    def test_event_type_stored(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="PARTY_ADDED",
            entity_type="PARTY",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert event.event_type == "PARTY_ADDED"

    def test_entity_type_stored(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="PARTY_ADDED",
            entity_type="PARTY",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert event.entity_type == "PARTY"

    def test_entity_id_stored(self) -> None:
        writer, _ = _make_writer()
        eid = uuid4()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=eid,
            tenant_id=uuid4(),
        )
        assert event.entity_id == eid

    def test_tenant_id_stored(self) -> None:
        writer, _ = _make_writer()
        tid = uuid4()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=tid,
        )
        assert event.tenant_id == tid

    def test_application_id_stored(self) -> None:
        writer, _ = _make_writer()
        app_id = uuid4()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
            application_id=app_id,
        )
        assert event.application_id == app_id

    def test_application_id_defaults_to_none(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert event.application_id is None

    def test_actor_id_stored(self) -> None:
        writer, _ = _make_writer()
        actor = uuid4()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
            actor_id=actor,
        )
        assert event.actor_id == actor

    def test_actor_type_defaults_to_user_when_actor_id_provided(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
        )
        assert event.actor_type == "USER"

    def test_actor_type_defaults_to_system_when_no_actor_id(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert event.actor_type == "SYSTEM"

    def test_explicit_actor_type_overrides_default(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            actor_type="SERVICE",
        )
        assert event.actor_type == "SERVICE"

    def test_event_data_stored(self) -> None:
        writer, _ = _make_writer()
        data = {"status": "DRAFT", "los_reference": "LOS-001"}
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
            event_data=data,
        )
        assert event.event_data == data

    def test_event_data_defaults_to_empty_dict(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert event.event_data == {}

    def test_multiple_records_added_to_session(self) -> None:
        writer, session = _make_writer()
        e1 = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        e2 = writer.record(
            event_type="PARTY_ADDED",
            entity_type="PARTY",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert session.add.call_count == 2
        session.add.assert_any_call(e1)
        session.add.assert_any_call(e2)

    def test_event_has_occurred_at(self) -> None:
        writer, _ = _make_writer()
        event = writer.record(
            event_type="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=uuid4(),
            tenant_id=uuid4(),
        )
        assert event.occurred_at is not None
        assert event.occurred_at.tzinfo is not None
