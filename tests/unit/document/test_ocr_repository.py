"""Unit tests for mil.document.ocr_repository — OCRResultRepository."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from mil.document.ocr_models import OCRResultRecord
from mil.document.ocr_repository import OCRResultRepository
from mil.kernel.providers.ocr import OCRResult, PageLayout, PageText


def _record() -> OCRResultRecord:
    result = OCRResult(
        document_ref="ref",
        pages=(
            PageText(
                page_number=1,
                text="text",
                layout=PageLayout(page_number=1, width_points=1.0, height_points=1.0),
                word_count=1,
            ),
        ),
        provider_version="v1",
        processed_at=datetime.now(UTC),
    )
    return OCRResultRecord.create(
        document_id=uuid4(),
        workflow_run_id=uuid4(),
        tenant_id=uuid4(),
        ocr_result=result,
    )


def _make_repo() -> tuple[OCRResultRepository, MagicMock]:
    session = MagicMock()
    return OCRResultRepository(session), session


class TestSave:
    def test_adds_and_flushes(self) -> None:
        repo, session = _make_repo()
        record = _record()
        repo.save(record)
        session.add.assert_called_once_with(record)
        session.flush.assert_called_once()

    def test_does_not_commit(self) -> None:
        repo, session = _make_repo()
        repo.save(_record())
        session.commit.assert_not_called()


class TestGetByDocumentAndVersion:
    def test_returns_existing_record(self) -> None:
        repo, session = _make_repo()
        record = _record()
        session.scalars.return_value.one_or_none.return_value = record
        assert repo.get_by_document_and_version(uuid4(), "v1") is record

    def test_returns_none_when_missing(self) -> None:
        repo, session = _make_repo()
        session.scalars.return_value.one_or_none.return_value = None
        assert repo.get_by_document_and_version(uuid4(), "v1") is None


class TestExists:
    def test_true_when_present(self) -> None:
        repo, session = _make_repo()
        session.scalars.return_value.one_or_none.return_value = _record()
        assert repo.exists_for_document_and_version(uuid4(), "v1") is True

    def test_false_when_absent(self) -> None:
        repo, session = _make_repo()
        session.scalars.return_value.one_or_none.return_value = None
        assert repo.exists_for_document_and_version(uuid4(), "v1") is False


class TestGetForDocument:
    def test_returns_list(self) -> None:
        repo, session = _make_repo()
        r1, r2 = _record(), _record()
        session.scalars.return_value = iter([r1, r2])
        assert repo.get_for_document(uuid4()) == [r1, r2]
