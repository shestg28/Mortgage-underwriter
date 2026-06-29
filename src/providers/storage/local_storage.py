"""
LocalStorageProvider — development filesystem-backed storage provider.

Stores documents in a local directory using content-addressed paths
(SHA-256 hash as the file name).  Intended for local development and
conformance testing.  Provides full ``StorageProvider`` contract compliance
including integrity verification.

MUST NOT be registered in staging or production containers.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from mil.kernel.providers.storage import StorageProvider, StorageReference

_DEFAULT_SUBDIR = "mil-local-storage"


class LocalStorageProvider(StorageProvider):
    """
    Filesystem-backed ``StorageProvider`` for local development.

    Documents are stored as flat files under ``base_path`` using the
    content hash as the file name (``<sha256_hex>.bin``).  Because the
    addressing is content-based, ``store()`` is naturally idempotent:
    writing the same content twice results in the same file path.

    Args:
        base_path: Directory in which to store documents.  Created
                   (including parents) if it does not already exist.
    """

    def __init__(self, base_path: str | Path | None = None) -> None:
        if base_path is None:
            import tempfile

            base_path = Path(tempfile.gettempdir()) / _DEFAULT_SUBDIR
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def store(self, content: bytes, content_hash: str) -> StorageReference:
        """
        Write ``content`` to a file named after ``content_hash``.

        Validates that the caller-supplied hash matches the actual SHA-256
        of ``content`` to catch accidental mismatches early.

        Returns:
            ``StorageReference`` with the absolute file path as the reference.

        Raises:
            ValueError:    If ``content_hash`` does not match the SHA-256 of
                           ``content``.
        """
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != content_hash:
            raise ValueError(
                f"Content hash mismatch: expected {content_hash!r}, computed {actual_hash!r}."
            )

        target = self._base_path / f"{content_hash}.bin"

        if not target.exists():
            target.write_bytes(content)
            stored_at = datetime.now(UTC)
        else:
            stat = target.stat()
            stored_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC)

        return StorageReference(
            reference=str(target),
            content_hash=content_hash,
            size_bytes=len(content),
            stored_at=stored_at,
        )

    def retrieve(self, reference: str) -> bytes:
        """
        Read and return the bytes stored at ``reference``.

        Raises:
            FileNotFoundError: If no file exists at ``reference``.
        """
        path = Path(reference)
        if not path.exists():
            raise FileNotFoundError(f"No stored content at reference: {reference!r}")
        return path.read_bytes()

    def verify_integrity(self, reference: str, expected_hash: str) -> bool:
        """
        Verify that the stored content matches ``expected_hash``.

        Returns ``False`` rather than raising if the file is missing.
        """
        try:
            content = self.retrieve(reference)
        except FileNotFoundError:
            return False
        actual = hashlib.sha256(content).hexdigest()
        return actual == expected_hash

    @property
    def base_path(self) -> Path:
        """The root directory where documents are stored."""
        return self._base_path
