"""
StorageProvider conformance tests.

Verifies that any concrete ``StorageProvider`` satisfies the interface contract
defined in ``mil.kernel.providers.storage``, including content-addressed
storage, idempotent writes, retrieval, and integrity verification.
"""

from __future__ import annotations

import hashlib

import pytest

from mil.kernel.providers.storage import StorageProvider, StorageReference


class TestStorageProviderInterfaceContract:
    """Verify the abstract interface structure."""

    def test_storage_provider_is_abstract(self) -> None:
        assert StorageProvider.__abstractmethods__ != set()

    def test_store_is_abstract(self) -> None:
        assert "store" in StorageProvider.__abstractmethods__

    def test_retrieve_is_abstract(self) -> None:
        assert "retrieve" in StorageProvider.__abstractmethods__

    def test_verify_integrity_is_abstract(self) -> None:
        assert "verify_integrity" in StorageProvider.__abstractmethods__

    def test_concrete_provider_is_subclass(self, storage_provider: StorageProvider) -> None:
        assert isinstance(storage_provider, StorageProvider)


class TestStorageProviderStore:
    """store() must return a valid StorageReference."""

    def test_returns_storage_reference(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert isinstance(ref, StorageReference)

    def test_reference_is_non_empty(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert ref.reference != ""

    def test_content_hash_echoed(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert ref.content_hash == sample_content_hash

    def test_size_bytes_correct(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert ref.size_bytes == len(sample_pdf_bytes)

    def test_stored_at_is_utc(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert ref.stored_at.tzinfo is not None

    def test_wrong_hash_raises(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
    ) -> None:
        wrong_hash = "a" * 64
        with pytest.raises((ValueError, Exception)):
            storage_provider.store(sample_pdf_bytes, wrong_hash)


class TestStorageProviderIdempotency:
    """Storing the same content twice must be idempotent."""

    def test_double_store_returns_same_reference(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref1 = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        ref2 = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert ref1.reference == ref2.reference
        assert ref1.content_hash == ref2.content_hash


class TestStorageProviderRetrieve:
    """retrieve() must return the original bytes."""

    def test_retrieve_returns_original_bytes(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        retrieved = storage_provider.retrieve(ref.reference)
        assert retrieved == sample_pdf_bytes

    def test_retrieve_unknown_reference_raises(self, storage_provider: StorageProvider) -> None:
        with pytest.raises(Exception):  # noqa: B017
            storage_provider.retrieve("nonexistent/reference/that/does/not/exist")

    def test_retrieve_different_contents_independently(
        self, storage_provider: StorageProvider
    ) -> None:
        content_a = b"document content A"
        content_b = b"document content B"
        hash_a = hashlib.sha256(content_a).hexdigest()
        hash_b = hashlib.sha256(content_b).hexdigest()

        ref_a = storage_provider.store(content_a, hash_a)
        ref_b = storage_provider.store(content_b, hash_b)

        assert storage_provider.retrieve(ref_a.reference) == content_a
        assert storage_provider.retrieve(ref_b.reference) == content_b
        assert ref_a.reference != ref_b.reference


class TestStorageProviderIntegrityVerification:
    """verify_integrity() must correctly validate stored content."""

    def test_verify_stored_content_returns_true(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        assert storage_provider.verify_integrity(ref.reference, sample_content_hash)

    def test_verify_wrong_hash_returns_false(
        self,
        storage_provider: StorageProvider,
        sample_pdf_bytes: bytes,
        sample_content_hash: str,
    ) -> None:
        ref = storage_provider.store(sample_pdf_bytes, sample_content_hash)
        wrong_hash = "b" * 64
        assert not storage_provider.verify_integrity(ref.reference, wrong_hash)

    def test_verify_nonexistent_reference_returns_false(
        self, storage_provider: StorageProvider
    ) -> None:
        assert not storage_provider.verify_integrity("nonexistent/reference", "a" * 64)


class TestStorageReferenceValidation:
    """StorageReference constructor validates its own constraints."""

    def test_empty_reference_raises(self) -> None:
        from datetime import UTC, datetime

        with pytest.raises(ValueError, match="reference"):
            StorageReference(
                reference="",
                content_hash="a" * 64,
                size_bytes=100,
                stored_at=datetime.now(UTC),
            )

    def test_negative_size_raises(self) -> None:
        from datetime import UTC, datetime

        with pytest.raises(ValueError, match="size_bytes"):
            StorageReference(
                reference="s3://bucket/key",
                content_hash="a" * 64,
                size_bytes=-1,
                stored_at=datetime.now(UTC),
            )

    def test_naive_datetime_raises(self) -> None:
        from datetime import datetime

        with pytest.raises(ValueError, match="stored_at"):
            StorageReference(
                reference="s3://bucket/key",
                content_hash="a" * 64,
                size_bytes=100,
                stored_at=datetime.now(),  # naive — no tzinfo
            )
