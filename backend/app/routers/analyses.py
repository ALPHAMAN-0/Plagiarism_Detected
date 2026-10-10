"""
Analyses router — run plagiarism detection.

POST /api/v1/analyses/detect
  - Loads a previously-uploaded document
  - Runs the chosen algorithm against the active corpus
  - Returns a sanitized report
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from ..schemas import DetectRequest, DetectResponse, ReportMatchOut
from ..services.detect_service import run_detection
from ..services.document_store import get_store
from ..services.reporting import report_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])


@router.post("/detect", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    store = get_store()
    doc = store.get_document(req.document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown document_id: {req.document_id}",
        )
    corpus_chunks = store.all_corpus_chunks()
    if not corpus_chunks:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Corpus is empty — add at least one document via /api/v1/corpus",
        )

    report = run_detection(
        document_text=doc.text,
        corpus_chunks=corpus_chunks,
        algorithm=req.algorithm,
        top_k=req.top_k,
        threshold=req.threshold,
    )
    payload = report_to_dict(report)
    return DetectResponse(
        document_id=req.document_id,
        algorithm=payload["algorithm"],
        matches=[ReportMatchOut(**m) for m in payload["matches"]],
        summary=payload["summary"],
    )
