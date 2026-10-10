"""
Corpus router — add documents to the reference corpus.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from ..schemas import CorpusAddRequest, CorpusAddResponse
from ..services.chunking import chunk_text
from ..services.document_store import get_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/corpus", tags=["corpus"])


@router.post("", response_model=CorpusAddResponse, status_code=status.HTTP_201_CREATED)
def add_to_corpus(req: CorpusAddRequest) -> CorpusAddResponse:
    """Chunk a previously-uploaded document and add it to the active corpus."""
    store = get_store()
    doc = store.get_document(req.document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown document_id: {req.document_id}",
        )
    chunks = chunk_text(doc.text)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document has no extractable text",
        )
    entry = store.add_corpus(name=req.name, chunks=chunks)
    return CorpusAddResponse(
        corpus_id=entry.corpus_id,
        name=entry.name,
        chunks=len(entry.chunks),
    )


@router.get("")
def list_corpora() -> dict:
    """List all registered corpora with chunk counts."""
    return {
        "corpora": [
            {"corpus_id": c.corpus_id, "name": c.name, "chunks": len(c.chunks)}
            for c in get_store().list_corpora()
        ]
    }
