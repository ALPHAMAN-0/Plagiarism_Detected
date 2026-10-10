"""
Hashing utilities — SHA-256 for file/text fingerprints.

These are used for:
  * Deduplication of uploaded documents
  * Logging without leaking document content
  * Index lookup keys
"""

from __future__ import annotations

import hashlib


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """Return the hex SHA-256 digest of the UTF-8 encoding of ``text``."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    """Stream-hash a file on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(64 * 1024), b""):
            h.update(block)
    return h.hexdigest()


__all__ = ["sha256_bytes", "sha256_text", "sha256_file"]
