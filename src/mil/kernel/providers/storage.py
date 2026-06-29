"""
StorageProvider interface for the MIL Platform.

Stores and retrieves immutable document files using content-addressed storage.
Every stored object is identified by a SHA-256 content hash, ensuring that
the reference uniquely identifies the content and that integrity can be
independently verified.

This module defines only the abstract interface and its data types.
Concrete implementations live in ``src/providers/storage/`` and are
registered via ``ProviderRegistry.register_storage()``.

Dependency rule: this module imports from the Python standard library only.
No bounded context code should be imported here.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Storage data types
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class StorageReference:
    """
    An immutable reference to a stored document.

    The ``reference`` field is the content-addressed identifier — typically
    a path or URI derived from the SHA-256 hash.  The ``content_hash`` field
    is the hex-encoded SHA-256 digest of the stored bytes.

    Because storage is content-addressed, two ``store`` calls with identical
    content and hash produce the same ``reference``.  Callers can use this
    idempotency property to safely retry uploads.

    Attributes:
        reference:    Unique content-addressed identifier (e.g. a storage
                      path, S3 key, or MinIO object name derived from the hash).
        content_hash: Hex-encoded SHA-256 digest of the stored content.
        size_bytes:   Size of the stored object in bytes.
        stored_at:    UTC timestamp when the object was first written.
    """

    reference: str
    content_hash: str
    size_bytes: int
    stored_at: datetime

    def __post_init__(self) -> None:
        if not self.reference:
            raise ValueError("reference cannot be empty")
        if not self.content_hash:
            raise ValueError("content_hash cannot be empty")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")
        if self.stored_at.tzinfo is None:
            raise ValueError("stored_at must be timezone-aware")


def _now_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Abstract StorageProvider interface
# ---------------------------------------------------------------------------


class StorageProvider(ABC):
    """
    Abstract interface for content-addressed document storage.

    Documents are stored once and never modified — the storage layer is
    append-only.  Retrieval is by reference (the content-addressed identifier
    returned by ``store``).  Integrity verification uses the SHA-256 digest.

    The interface is engine-agnostic: concrete implementations may write to
    the local filesystem, MinIO, AWS S3, Azure Blob Storage, or GCS without
    any change to the calling business logic.

    Idempotency guarantee: calling ``store(content, hash)`` with the same
    content and hash MUST be idempotent.  If the object already exists, the
    provider returns a ``StorageReference`` describing the existing object.
    """

    @abstractmethod
    def store(self, content: bytes, content_hash: str) -> StorageReference:
        """
        Store document bytes using content-addressed storage.

        Args:
            content:      Raw document bytes to persist.
            content_hash: Hex-encoded SHA-256 digest of ``content``, computed
                          by the caller before the call.  The provider MUST
                          use this value as the addressing key.

        Returns:
            ``StorageReference`` with the content-addressed identifier and
            metadata.

        Raises:
            ProviderError: If the write fails.
            ValueError:    If ``content_hash`` does not match the SHA-256 of
                           ``content``.
        """

    @abstractmethod
    def retrieve(self, reference: str) -> bytes:
        """
        Retrieve document bytes by storage reference.

        Args:
            reference: The ``StorageReference.reference`` value returned by
                       a prior ``store`` call.

        Returns:
            The raw document bytes.

        Raises:
            ProviderError: If the object does not exist or cannot be retrieved.
        """

    @abstractmethod
    def verify_integrity(self, reference: str, expected_hash: str) -> bool:
        """
        Verify that stored content matches the expected SHA-256 digest.

        Args:
            reference:     The storage reference to verify.
            expected_hash: The hex-encoded SHA-256 digest the content must match.

        Returns:
            ``True`` if the stored content hash matches ``expected_hash``.
            ``False`` if the content is missing or the hash does not match.

        Note:
            This method MUST NOT raise on missing content — it should return
            ``False`` so callers can handle the case gracefully.
        """
