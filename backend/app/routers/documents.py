"""
Documents router — multipart upload, ingest, persist in store.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from ..config import get_settings
from ..schemas import DocumentUploadResponse
from ..services.chunking import chunk_text
from ..services.document_store import get_store
from ..services.hashing import sha256_bytes
from ..services.ingest import IngestError, extract_text
from ..services.security import (
    FileValidationError,
    safe_filename,
    validate_extension,
    validate_size,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Upload a single .txt / .pdf / .docx file. Returns document_id + stats."""
    settings = get_settings()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename",
        )

    # Validate filename (defense against path-traversal)
    try:
        clean_name = safe_filename(file.filename)
        ext = validate_extension(clean_name)
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Read the body (with size cap)
    payload = await file.read()
    try:
        validate_size(len(payload), max_bytes=settings.max_upload_bytes)
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc

    # Extract text
    try:
        text = extract_text(payload, f"file.{ext}")
    except IngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    # Persist
    sha = sha256_bytes(payload)
    doc = get_store().add_document(
        filename=clean_name,
        text=text,
        sha256=sha,
        size=len(payload),
    )

    return DocumentUploadResponse(
        document_id=doc.document_id,
        filename=doc.filename,
        sha256=doc.sha256,
        size=doc.size,
        text_length=len(text),
        chunks=len(chunk_text(text)),
    )
