"""
Burstiness metric — variation in sentence length.

Humans write with high burstiness (mix of short and long sentences); LLMs
tend to produce uniform sentence lengths. Computed as the coefficient of
variation (stdev / mean) of per-sentence token counts.
"""

from __future__ import annotations

import numpy as np

from .features import split_sentences, tokenize


def burstiness(text: str) -> float:
    """Coefficient of variation of sentence lengths. 0 if no sentences."""
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    lens = [len(tokenize(s)) for s in sentences]
    if not lens:
        return 0.0
    mean = float(np.mean(lens))
    if mean == 0:
        return 0.0
    return float(np.std(lens) / mean)


__all__ = ["burstiness"]
