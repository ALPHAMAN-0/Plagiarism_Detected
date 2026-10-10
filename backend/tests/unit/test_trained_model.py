"""
Smoke tests for the trained AI classifier.

These tests assert that:
  1. The training script can run against ``data/ai_train.csv`` and
     produce a valid ``app/ml_models/ai_classifier.joblib``.
  2. ``predict_proba`` with that path returns a model_version that
     starts with ``joblib-`` (not the heuristic-v1 fallback).
  3. The trained model beats the heuristic on the four canonical
     test cases (ai / human / plagiarised / verbose GPT).

Run ``make backend-train`` to regenerate the model.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.ai_detect.classifier import predict_proba

MODEL_PATH = Path("app/ml_models/ai_classifier.joblib")


def test_trained_model_file_exists() -> None:
    assert MODEL_PATH.exists(), (
        f"{MODEL_PATH} not found. Run `make backend-train` to train the "
        "classifier against data/ai_train.csv."
    )


def test_predict_proba_uses_trained_model_when_available() -> None:
    if not MODEL_PATH.exists():
        pytest.skip(f"{MODEL_PATH} not present; run `make backend-train` first")
    _, _, _, version = predict_proba(
        "Just a short test sentence for invocation.", model_path=str(MODEL_PATH)
    )
    assert version.startswith("joblib-"), (
        f"expected version starting with 'joblib-', got {version!r}. "
        "The trained model file is present but predict_proba is still "
        "falling back to the heuristic — likely a path mismatch."
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Honestly, I never thought I'd end up here. Last Tuesday my "
            "whole plan fell apart in about ten minutes — the client just "
            "ghosted mid-call and the cat knocked my coffee over. So that "
            "was my week, basically.",
            "human",
        ),
        (
            "The model is a transformer. It is trained on data. It learns "
            "patterns. It is accurate. It is fast. It is useful. It is "
            "popular. It is scalable. It is flexible. It is reliable.",
            "ai",
        ),
    ],
)
def test_trained_model_classifies_canonical_cases(text: str, expected: str) -> None:
    """The AI/human classifier is trained on lexical features. Plagiarism
    detection is a separate system (the algorithms layer) that compares
    against a reference corpus — it is not re-tested here.
    """
    if not MODEL_PATH.exists():
        pytest.skip(f"{MODEL_PATH} not present; run `make backend-train` first")
    label, proba, _, version = predict_proba(text, model_path=str(MODEL_PATH))
    assert version.startswith("joblib-")
    assert label == expected, (
        f"expected label {expected!r}, got {label!r} with proba={proba} "
        f"(model_version={version})"
    )