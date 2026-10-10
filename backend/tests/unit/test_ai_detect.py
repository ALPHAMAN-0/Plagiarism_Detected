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


# ---------------------------------------------------------------------------
# Heuristic correctness — label-specific assertions (RED until AI-detect fix)
# ---------------------------------------------------------------------------
#
# The previous tests only asserted the structural contract (three classes,
# probabilities sum to 1). They did not check that the right class wins.
# The following tests pin label-level behaviour for clearly-classifiable
# inputs. They are the regression net for the P(ai) = 0.02 floor bug
# where the heuristic could never label a document as "ai".


def _top_label(proba: dict) -> str:
    return max(proba, key=lambda k: proba[k])


def test_predict_proba_flags_uniform_low_burstiness_as_ai() -> None:
    """Uniform short sentences + low burstiness + low TTR is the
    AI-detect canonical case. The heuristic currently returns P(ai) ~ 0.02
    (floored) and labels it 'human'. The fix must make P(ai) the top
    probability for this input.
    """
    text = (
        "The model is a transformer. It is trained on data. "
        "It learns patterns. It generates text. It is accurate. "
        "It is fast. It is useful. It is popular. It is modern. "
        "It is reliable. It is efficient. It is scalable."
    )
    label, proba, _, _ = predict_proba(text, model_path="")
    assert _top_label(proba) == "ai", (
        f"expected label 'ai' for uniform low-burstiness text, got {label!r} "
        f"with proba={proba}"
    )
    assert proba["ai"] >= 0.5, f"expected P(ai) >= 0.5, got {proba['ai']:.3f}"


def test_predict_proba_flags_gpt_style_verbose_as_ai() -> None:
    """Verbose GPT-style text has burstiness 0.25 (low, AI-ish) but TTR 0.79
    (high, human-ish). The previous bug floored it at P(ai) ~ 0.02. The
    fix must lift P(ai) well above the plagiarised class — decisive AI
    detection on verbose templated text is the trained model's job,
    not the heuristic's.
    """
    text = (
        "It is important to note that artificial intelligence has fundamentally "
        "transformed the way in which we approach complex problems. "
        "Furthermore, the development of large language models has enabled "
        "significant advances in natural language processing. "
        "Additionally, these models can be applied to a wide range of tasks. "
        "Moreover, the implications of this technology are far-reaching. "
        "Consequently, it is essential to consider both the benefits and the risks."
    )
    label, proba, _, _ = predict_proba(text, model_path="")
    # The bug was P(ai) = 0.02. The fix must lift it noticeably above
    # the previous floor.
    assert proba["ai"] >= 0.15, (
        f"expected P(ai) >= 0.15 (above the previous floor), got {proba['ai']:.3f}"
    )
    assert proba["ai"] > proba["plagiarised"], (
        f"P(ai)={proba['ai']:.3f} should beat P(plag)={proba['plagiarised']:.3f}"
    )


def test_predict_proba_preserves_human_label_for_bursty_text() -> None:
    """Bursty, varied human-style text must still be classified as 'human'.
    Regression guard: the AI-detect fix must not flip this case.
    """
    text = (
        "Honestly, I never thought I'd end up here. "
        "Last Tuesday my whole plan fell apart in about ten minutes — the client "
        "just ghosted mid-call, and the next thing I know I'm staring at my "
        "laptop wondering if I should have been a plumber instead. "
        "Weird thing is, the cat loved it. "
        "She got the whole desk to herself, knocked my coffee over, and looked "
        "deeply satisfied about the whole situation. So that was my week, basically."
    )
    label, proba, _, _ = predict_proba(text, model_path="")
    assert _top_label(proba) == "human", (
        f"expected label 'human' for bursty personal text, got {label!r} "
        f"with proba={proba}"
    )
    assert proba["human"] >= 0.5


def test_predict_proba_preserves_plagiarised_label_for_famous_passage() -> None:
    """A famous verbatim passage (Dickens) must still be flagged as
    'plagiarised'. Regression guard for the AI-detect fix.
    """
    text = (
        "It was the best of times, it was the worst of times, it was the age of "
        "wisdom, it was the age of foolishness, it was the epoch of belief, it "
        "was the epoch of incredulity, it was the season of Light, it was the "
        "season of Darkness, it was the spring of hope, it was the winter of "
        "despair, we had everything before us, we had nothing before us, we were "
        "all going direct to Heaven, we were all going direct the other way."
    )
    label, proba, _, _ = predict_proba(text, model_path="")
    assert _top_label(proba) == "plagiarised", (
        f"expected label 'plagiarised' for famous verbatim passage, got {label!r} "
        f"with proba={proba}"
    )
    assert proba["plagiarised"] >= 0.4
