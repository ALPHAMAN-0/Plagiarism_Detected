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

    Heuristics (revised — perplexity is intentionally NOT used as a primary
    signal because the default ``distilgpt2`` model is too small to
    distinguish AI from human text reliably; it raises high perplexity on
    text it considers unlikely, which conflates unfamiliar human writing
    with AI output. Instead we lean on the lexical features that
    hold up across the canonical test cases).

      * AI:
          - low burstiness  (uniform sentence length)
          - high stopword ratio  (filler-heavy)
          - low TTR  (repetitive vocabulary)
          - short avg sentence length  (templated phrasing)
      * Human:
          - high burstiness  (varied sentence length)
          - high TTR  (rich vocabulary)
          - mixed stopword ratio
      * Plagiarised:
          - very low burstiness  (one long sentence, copied verbatim)
          - very high avg sentence length
          - high stopword ratio
    """
    burst = features.burstiness
    ttr = features.type_token_ratio
    avg_len = features.avg_sentence_length
    stop = features.stopword_ratio

    # --- P(ai) -----------------------------------------------------------
    # Each factor is a soft [0, 1] gate. The product is small unless ALL
    # the AI signals agree. The floor on P(ai) is 0.02 (mirrors the
    # previous floor to keep behaviour stable on uninformative input).
    p_ai_low_burst = 1.0 / (1.0 + np.exp((burst - 0.45) / 0.12))
    p_ai_high_stop = 1.0 / (1.0 + np.exp((0.42 - stop) / 0.05))
    p_ai_low_ttr = 1.0 / (1.0 + np.exp((ttr - 0.75) / 0.10))
    p_ai_short = 1.0 / (1.0 + np.exp((avg_len - 12.0) / 4.0))
    p_ai = p_ai_low_burst * p_ai_high_stop * p_ai_low_ttr * p_ai_short
    p_ai = float(np.clip(p_ai, 0.02, 0.95))

    # --- P(human) --------------------------------------------------------
    # Burstiness is the strongest human signal; TTR is a secondary
    # contributor. The previous coefficients (1.1 * burst + 0.6 * ttr)
    # were over-generous: verbose AI text with high TTR (because the
    # writer uses a varied vocabulary even when templated) was being
    # misclassified as human. Tighter coefficients still lock in
    # bursty human text at >= 0.9 but let the AI signal compete on
    # verbose GPT-style prose.
    p_human = float(
        np.clip(0.15 + 1.0 * burst + 0.4 * ttr - 0.5 * (1.0 - stop), 0.02, 0.95)
    )

    # --- P(plagiarised) --------------------------------------------------
    # Strong when there is essentially no burstiness (one giant copied
    # sentence) AND the avg sentence length is large.
    p_plag_low_burst = 1.0 / (1.0 + np.exp((burst - 0.15) / 0.05))
    p_plag_long = 1.0 / (1.0 + np.exp((40.0 - avg_len) / 10.0))
    p_plag = float(np.clip(p_plag_low_burst * p_plag_long, 0.02, 0.95))

    # Renormalise so the three probabilities sum to 1.
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
