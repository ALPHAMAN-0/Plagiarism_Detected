"""
Tests for AI-detect feature engineering and classifier.

RED tests — will fail until features.py / classifier.py are implemented.
"""

from __future__ import annotations

import math

import numpy as np

from app.services.ai_detect.burstiness import burstiness
from app.services.ai_detect.classifier import CLASSES, predict_proba
from app.services.ai_detect.features import (
    extract_features,
    lexical_features,
    split_sentences,
    tokenize,
)
from app.services.ai_detect.perplexity import mean_perplexity


def test_split_sentences_basic() -> None:
    out = split_sentences("Hello world. How are you? Fine!")
    assert out == ["Hello world.", "How are you?", "Fine!"]


def test_tokenize_lowercases() -> None:
    assert tokenize("Hello World") == ["hello", "world"]


def test_lexical_features_returns_finite_values() -> None:
    f = lexical_features("This is a test. Just a small test of the features.")
    arr = f.to_array()
    assert arr.shape == (6,)
    assert np.all(np.isfinite(arr))


def test_burstiness_zero_for_uniform_lengths() -> None:
    text = "A b c. D e f. G h i. J k l."
    assert burstiness(text) == 0.0 or burstiness(text) < 0.05


def test_burstiness_higher_for_mixed_lengths() -> None:
    short = "Hi. Hi. Hi. Hi. Hi."
    long = "This is a much longer sentence that contains many words. Tiny. " * 20
    assert burstiness(long) > burstiness(short)


def test_extract_features_returns_full_vector() -> None:
    f = extract_features(
        "The quick brown fox jumps over the lazy dog. "
        "Photosynthesis converts light energy into chemical energy. "
        "I wandered lonely as a cloud."
    )
    arr = f.to_array()
    assert arr.shape == (6,)
    # All features must be finite (perplexity falls back gracefully)
    assert np.all(np.isfinite(arr))


def test_perplexity_returns_finite_pair() -> None:
    text = "The capital of France is Paris. It is a beautiful city."
    mean, std = mean_perplexity(text)
    assert math.isfinite(mean)
    assert math.isfinite(std)
    assert 1.0 < mean < 1e5


def test_predict_proba_returns_three_class_dict() -> None:
    label, proba, features, version = predict_proba(
        "This is a short test document. " * 5,
        model_path="",
    )
    assert label in CLASSES
    assert set(proba.keys()) == set(CLASSES)
    # Probabilities sum to (approximately) 1
    assert abs(sum(proba.values()) - 1.0) < 1e-3
    assert all(0.0 <= p <= 1.0 for p in proba.values())
    assert isinstance(version, str)
    assert features["avg_sentence_length"] > 0


def test_predict_proba_handles_very_short_input() -> None:
    label, proba, _, _ = predict_proba("hi.", model_path="")
    assert label in CLASSES
    assert abs(sum(proba.values()) - 1.0) < 1e-3
