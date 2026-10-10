"""
Feature extraction for AI / human / plagiarism classification.

Features are intentionally cheap and interpretable so the model can be
debugged and so we can run them on any hardware:

  * perplexity_mean        — mean per-token perplexity from distilgpt2
  * perplexity_std         — std-dev of per-sentence perplexities
  * burstiness             — stdev / mean of sentence token counts
  * type_token_ratio       — vocabulary richness
  * avg_sentence_length    — mean sentence length (words)
  * stopword_ratio         — stopwords / total tokens

If the transformers library isn't available or the model fails to load,
the perplexity features fall back to neutral defaults so the rest of the
pipeline keeps working.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np

# Tiny built-in English stopword list — keeps the module self-contained.
_STOPWORDS = frozenset(
    """a about above after again against all am an and any are as at be because been
    before being below between both but by can did do does doing don during each few
    for from further had has have having he her here hers herself him himself his how
    i if in into is it its itself just me more most my myself no nor not now of off
    on once only or other our ours ourselves out over own same she should so some such
    than that the their theirs them themselves then there these they this those through
    to too under until up very was we were what when where which while who whom why
    will with would you your yours yourself yourselves""".split()
)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    return [s.strip() for s in _SENTENCE_END.split(cleaned) if s.strip()]


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


@dataclass(frozen=True)
class FeatureVector:
    perplexity_mean: float
    perplexity_std: float
    burstiness: float
    type_token_ratio: float
    avg_sentence_length: float
    stopword_ratio: float

    def to_array(self) -> np.ndarray:
        return np.array(
            [
                self.perplexity_mean,
                self.perplexity_std,
                self.burstiness,
                self.type_token_ratio,
                self.avg_sentence_length,
                self.stopword_ratio,
            ],
            dtype=np.float32,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "perplexity_mean": self.perplexity_mean,
            "perplexity_std": self.perplexity_std,
            "burstiness": self.burstiness,
            "type_token_ratio": self.type_token_ratio,
            "avg_sentence_length": self.avg_sentence_length,
            "stopword_ratio": self.stopword_ratio,
        }


def lexical_features(text: str) -> FeatureVector:
    """Compute all non-perplexity features (works without a model)."""
    sentences = split_sentences(text)
    tokens = tokenize(text)

    if sentences:
        sent_lens = [len(tokenize(s)) for s in sentences]
        avg = float(np.mean(sent_lens))
        std = float(np.std(sent_lens))
        burst = float(std / avg) if avg > 0 else 0.0
    else:
        avg, std, burst = 0.0, 0.0, 0.0

    if tokens:
        ttr = len(set(tokens)) / len(tokens)
        stop_ratio = sum(1 for t in tokens if t in _STOPWORDS) / len(tokens)
    else:
        ttr, stop_ratio = 0.0, 0.0

    # Perplexity placeholders — filled in by `enrich_with_perplexity`.
    return FeatureVector(
        perplexity_mean=50.0,  # neutral default (mid-range for human & AI)
        perplexity_std=10.0,
        burstiness=burst,
        type_token_ratio=ttr,
        avg_sentence_length=avg,
        stopword_ratio=stop_ratio,
    )


def enrich_with_perplexity(features: FeatureVector, text: str) -> FeatureVector:
    """Replace the perplexity fields with model-derived values.

    Falls back to the defaults if transformers / torch are unavailable.
    """
    try:
        from .perplexity import mean_perplexity  # local import to avoid hard dep
        ppl_mean, ppl_std = mean_perplexity(text)
    except Exception:  # noqa: BLE001
        return features
    return FeatureVector(
        perplexity_mean=ppl_mean,
        perplexity_std=ppl_std,
        burstiness=features.burstiness,
        type_token_ratio=features.type_token_ratio,
        avg_sentence_length=features.avg_sentence_length,
        stopword_ratio=features.stopword_ratio,
    )


def extract_features(text: str) -> FeatureVector:
    """One-shot feature extraction used by the predict endpoint."""
    f = lexical_features(text)
    return enrich_with_perplexity(f, text)


__all__ = [
    "FeatureVector",
    "extract_features",
    "lexical_features",
    "enrich_with_perplexity",
    "split_sentences",
    "tokenize",
]
