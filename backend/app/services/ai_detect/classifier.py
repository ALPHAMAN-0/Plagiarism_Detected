"""
3-class classifier (human / ai / plagiarised).

Pipeline: StandardScaler → LogisticRegression. Trained on a small labelled
fixture set; persisted to ``app/ml_models/ai_classifier.joblib`` via joblib.

If no model file is present we run a deterministic heuristic classifier
that still returns reasonable probabilities — this keeps the API useful
out-of-the-box even before training has happened.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np

from .features import FeatureVector, extract_features

logger = logging.getLogger(__name__)

MODEL_VERSION = "heuristic-v1"  # overwritten once a real model is loaded
CLASSES: tuple[Literal["human", "ai", "plagiarised"], ...] = ("human", "ai", "plagiarised")


@lru_cache(maxsize=1)
def _load_model(path: str) -> tuple[Any, str] | None:
    """Load a persisted sklearn pipeline; return None if file is missing."""
    if not path:
        return None
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    try:
        model = joblib.load(p)
    except Exception as exc:
        logger.warning("ai_classifier.load_failed: %s (%s)", path, exc)
        return None
    return model, f"joblib-{p.stat().st_mtime:.0f}"


def _heuristic_proba(features: FeatureVector) -> dict[str, float]:
    """
    Deterministic, transparent fallback.

    Heuristics:
      * Low perplexity + low burstiness → AI
      * High stopword ratio + short avg sentence length → AI
      * Very high ttr + long sentences → human
      * Otherwise → human with mild plagiarism tilt
    """
    ppl = features.perplexity_mean
    burst = features.burstiness
    ttr = features.type_token_ratio
    avg_len = features.avg_sentence_length
    stop = features.stopword_ratio

    # Sigmoid-style mapping to [0, 1] for each class
    p_ai = 1.0 / (1.0 + np.exp((ppl - 40.0) / 8.0))  # low ppl ⇒ more AI
    p_ai *= 1.0 / (1.0 + np.exp((burst - 0.5) / 0.15))  # low burst ⇒ more AI
    p_ai *= 1.0 / (1.0 + np.exp((avg_len - 18.0) / 3.0))  # long sents ⇒ less AI
    p_ai = float(np.clip(p_ai, 0.02, 0.95))

    p_human = float(np.clip(0.5 + 0.4 * burst + 0.2 * ttr - 0.3 * (1.0 - stop), 0.02, 0.95))
    p_plag = max(0.02, 1.0 - p_ai - p_human)
    # Renormalise
    total = p_ai + p_human + p_plag
    return {
        "ai": p_ai / total,
        "human": p_human / total,
        "plagiarised": p_plag / total,
    }


def predict_proba(
    text: str, model_path: str
) -> tuple[str, dict[str, float], dict[str, float], str]:
    """
    Return (label, probabilities, features_dict, model_version).
    """
    features = extract_features(text)
    features_dict = features.to_dict()
    loaded = _load_model(model_path)
    if loaded is None:
        proba = _heuristic_proba(features)
        version = MODEL_VERSION
    else:
        model, version = loaded
        try:
            arr = features.to_array().reshape(1, -1)
            probs = model.predict_proba(arr)[0]
            classes = list(model.classes_)
            proba = {str(c).lower(): float(p) for c, p in zip(classes, probs, strict=False)}
            # Ensure all three classes are present
            for c in CLASSES:
                proba.setdefault(c, 0.0)
        except Exception as exc:
            logger.warning("ai_classifier.predict_failed: %s", exc)
            proba = _heuristic_proba(features)
            version = MODEL_VERSION

    label = max(proba, key=lambda k: proba[k])
    return label, proba, features_dict, version


__all__ = ["CLASSES", "MODEL_VERSION", "predict_proba"]
