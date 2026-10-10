"""
Ingest service — convert uploaded files (txt / pdf / docx) to plain text.

All inputs are byte strings; no filesystem state lives here.
"""

from __future__ import annotations

import io
import logging

from .security import SUPPORTED_EXTENSIONS, FileValidationError, validate_extension

logger = logging.getLogger(__name__)


class IngestError(ValueError):
    """Raised when a file cannot be ingested."""


def extract_text(payload: bytes, filename: str) -> str:
    """
    Extract plain text from ``payload`` (bytes) given its original filename.

    The file extension drives the parser. Unknown or unsupported extensions
    raise ``IngestError``.
    """
    ext = validate_extension(filename, SUPPORTED_EXTENSIONS)
    if ext == "txt":
        return _extract_txt(payload)
    if ext == "pdf":
        return _extract_pdf(payload)
    if ext == "docx":
        return _extract_docx(payload)
    raise IngestError(f"Unsupported extension: {ext}")


# ---------- format-specific helpers ----------


def _extract_txt(payload: bytes) -> str:
    """Decode plain text with the most permissive encoding strategy."""
    if not payload:
        return ""
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        # Try a couple of common fallbacks
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                return payload.decode(enc)
            except UnicodeDecodeError:
                continue
        # Last resort: replace errors
        return payload.decode("utf-8", errors="replace")


def _extract_pdf(payload: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise IngestError("pypdf not installed") from exc
    reader = PdfReader(io.BytesIO(payload))
    chunks: list[str] = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("pdf_page_extract_failed", error=str(exc))
    return "\n".join(chunks).strip()


def _extract_docx(payload: bytes) -> str:
    try:
        import docx2txt
    except ImportError as exc:  # pragma: no cover
        raise IngestError("docx2txt not installed") from exc
    text = docx2txt.process(io.BytesIO(payload))
    return (text or "").strip()


__all__ = ["SUPPORTED_EXTENSIONS", "IngestError", "extract_text"]
