"""
Security helpers — file validation, path traversal guards, output sanitization.

All functions here are pure and dependency-free, so they can be unit-tested
without spinning up the FastAPI app.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

# Allowlist mirrors the default in app.config.Settings.allowed_extensions.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({"pdf", "txt", "docx"})


class FileValidationError(ValueError):
    """Raised when a file fails validation (size, extension, etc.)."""


class PathTraversalError(ValueError):
    """Raised when a path resolves outside the allowed base directory."""


# ---------- filename sanitization ----------

_FILENAME_INVALID = re.compile(r"[^\w.\-]+", re.UNICODE)


def safe_filename(name: str) -> str:
    """
    Reduce an arbitrary user-supplied filename to a single safe basename.

    - Strips directory components (forward, backward, and URL-style slashes).
    - Normalizes unicode (NFKC) to defeat homoglyph tricks.
    - Strips path segments like ``..`` and ``.``.
    - Removes characters outside ``[\\w.-]``.
    - Raises ``FileValidationError`` for empty or dotfile-only results.

    The result is intended to be combined with a UUID prefix when persisted.
    """
    if not name:
        raise FileValidationError("Filename is empty")

    normalized = unicodedata.normalize("NFKC", name)
    # Drop directory components
    basename = normalized.replace("\\", "/").split("/")[-1]
    if basename in {".", "..", ""}:
        raise FileValidationError(f"Unsafe filename: {name!r}")
    # Reject dotfiles (e.g. .hidden, .env)
    if basename.startswith("."):
        raise FileValidationError(f"Dotfile rejected: {name!r}")
    # Remove disallowed characters
    cleaned = _FILENAME_INVALID.sub("_", basename).strip("._")
    if not cleaned or cleaned in {".", ".."}:
        raise FileValidationError(f"Unsafe filename: {name!r}")
    return cleaned


def validate_extension(filename: str, allowed: frozenset[str] = SUPPORTED_EXTENSIONS) -> str:
    """
    Return the lowercased extension if allowed, else raise FileValidationError.

    The extension is the substring after the final ``.`` in the basename
    (case-insensitive). No extension at all is rejected.
    """
    basename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." not in basename:
        raise FileValidationError(f"File has no extension: {filename!r}")
    ext = basename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise FileValidationError(
            f"Unsupported extension {ext!r}. Allowed: {sorted(allowed)}"
        )
    return ext


def validate_size(size: int, max_bytes: int) -> None:
    """Raise if ``size`` exceeds ``max_bytes``."""
    if size < 0:
        raise FileValidationError("Negative size")
    if size > max_bytes:
        raise FileValidationError(
            f"File too large: {size} bytes (max {max_bytes})"
        )


# ---------- path-traversal guard ----------

def safe_join(base: Path | str, *parts: str) -> Path:
    """
    Join ``parts`` to ``base`` and assert the result stays inside ``base``.

    Raises ``PathTraversalError`` if the resolved path escapes the base.
    Resolves symlinks before checking, so symlink-based escapes are blocked.
    """
    base_resolved = Path(base).resolve()
    candidate = (base_resolved.joinpath(*parts)).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise PathTraversalError(
            f"Path escapes base directory: {candidate!s} not under {base_resolved!s}"
        ) from exc
    return candidate


# ---------- HTML / text sanitization ----------

_HTML_ESCAPE_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
}


def escape_html(text: str) -> str:
    """Escape HTML-significant characters in user-supplied text."""
    return "".join(_HTML_ESCAPE_MAP.get(ch, ch) for ch in text)


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "FileValidationError",
    "PathTraversalError",
    "safe_filename",
    "validate_extension",
    "validate_size",
    "safe_join",
    "escape_html",
]
