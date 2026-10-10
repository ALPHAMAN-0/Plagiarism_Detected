"""
RED tests for ingest + security services.

User journeys:
  As a user, I can drop a .txt/.pdf/.docx file and the API extracts its text.
  As a security engineer, no malicious filename or oversized file slips through.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.services.ingest import extract_text, SUPPORTED_EXTENSIONS
from app.services.security import (
    safe_filename,
    safe_join,
    validate_extension,
    validate_size,
    FileValidationError,
    PathTraversalError,
)


# ---------- happy path ----------

def test_extract_text_from_txt_bytes() -> None:
    payload = b"Hello, world.\nThis is a test document."
    text = extract_text(payload, "sample.txt")
    assert "Hello, world" in text
    assert "test document" in text


def test_supported_extensions_includes_txt_pdf_docx() -> None:
    assert "txt" in SUPPORTED_EXTENSIONS
    assert "pdf" in SUPPORTED_EXTENSIONS
    assert "docx" in SUPPORTED_EXTENSIONS


# ---------- security ----------

def test_safe_filename_strips_path_traversal() -> None:
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("/abs/path/file.txt") == "file.txt"
    assert safe_filename("..\\..\\windows\\sys.txt") == "sys.txt"


def test_safe_filename_rejects_empty_or_dotfiles() -> None:
    with pytest.raises(FileValidationError):
        safe_filename("..")
    with pytest.raises(FileValidationError):
        safe_filename(".hidden")
    with pytest.raises(FileValidationError):
        safe_filename("")


def test_safe_join_rejects_escape_attempts(tmp_path: Path) -> None:
    base = tmp_path / "uploads"
    base.mkdir()
    # Good case
    out = safe_join(base, "abc.txt")
    assert out == (base / "abc.txt").resolve()
    # Bad case
    with pytest.raises(PathTraversalError):
        safe_join(base, "../../etc/passwd")


def test_validate_extension_allows_known() -> None:
    for ext in ("a.txt", "b.PDF", "c.docx"):
        validate_extension(ext)  # does not raise


def test_validate_extension_rejects_unknown() -> None:
    with pytest.raises(FileValidationError):
        validate_extension("evil.exe")
    with pytest.raises(FileValidationError):
        validate_extension("no_extension")


def test_validate_size_rejects_oversized() -> None:
    with pytest.raises(FileValidationError):
        validate_size(11 * 1024 * 1024, max_bytes=10 * 1024 * 1024)
    # Under the cap is fine
    validate_size(1024, max_bytes=10 * 1024 * 1024)
