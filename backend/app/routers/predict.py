"""
Predict router — POST /api/v1/predict returns a 3-class probability.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from ..config import get_settings
from ..schemas import PredictRequest, PredictResponse
from ..services.ai_detect.classifier import predict_proba
from ..services.document_store import get_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predict", tags=["predict"])


@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    settings = get_settings()
    store = get_store()
    doc = store.get_document(req.document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown document_id: {req.document_id}",
        )
    label, proba, features, version = predict_proba(
        doc.text, model_path=str(settings.ai_classifier_path)
    )
    return PredictResponse(
        document_id=req.document_id,
        label=label,  # type: ignore[arg-type]
        probabilities=proba,
        features=features,
        model_version=version,
    )
