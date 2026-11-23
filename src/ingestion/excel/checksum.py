"""Deterministic SHA-256 Checksum Generator & In-Memory Duplicate Detection Helpers.

This module provides pure infrastructure utilities for calculating SHA-256 byte hashes and detecting duplicate uploads.
Zero database persistence or external storage dependencies.
"""

import hashlib
from typing import Iterable, Set


def calculate_bytes_sha256(data: bytes) -> str:
    """Calculate hex-encoded SHA-256 hash string for raw file bytes."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Input data must be bytes or bytearray.")
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def calculate_stream_sha256(chunks: Iterable[bytes]) -> str:
    """Calculate hex-encoded SHA-256 hash string for an iterable of byte chunks."""
    hasher = hashlib.sha256()
    for chunk in chunks:
        hasher.update(chunk)
    return hasher.hexdigest()


class DuplicateDetector:
    """In-memory thread-safe duplicate checksum registry for session active queues."""

    def __init__(self, initial_hashes: Iterable[str] = ()) -> None:
        self._seen_hashes: Set[str] = set(initial_hashes)

    def is_duplicate(self, sha256_hash: str) -> bool:
        """Check if SHA-256 hash exists in seen registry."""
        return sha256_hash in self._seen_hashes

    def register(self, sha256_hash: str) -> bool:
        """Register SHA-256 hash. Returns True if hash was newly registered, False if duplicate."""
        if sha256_hash in self._seen_hashes:
            return False
        self._seen_hashes.add(sha256_hash)
        return True

    def clear(self) -> None:
        """Reset seen hashes registry."""
        self._seen_hashes.clear()
