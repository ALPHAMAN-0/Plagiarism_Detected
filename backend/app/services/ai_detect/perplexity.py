"""
Per-token perplexity from a small causal LM (default: distilgpt2).

We use perplexity as one feature in a feature-engineered classifier
rather than the sole signal — the burstiness/vocabulary features catch
things a perplexity-only detector misses.

The model is loaded once per process via lru_cache.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

MODEL_NAME_DEFAULT = "distilgpt2"


@lru_cache(maxsize=1)
def _load_model(name: str):
    """Load tokenizer + model. Cached for the process lifetime.

    `revision="main"` pins the Hugging Face Hub snapshot to a specific ref
    so a malicious or accidental upstream change cannot silently swap
    model weights. Bump this when intentionally upgrading.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(name, revision="main")  # noqa: S615
    model = AutoModelForCausalLM.from_pretrained(name, revision="main")  # noqa: S615
    model.eval()
    return tok, model, torch


def _ensure_str(text: str, max_chars: int = 8000) -> str:
    """Truncate very long documents to fit the model's context window."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _sentence_perplexities(text: str, model_name: str = MODEL_NAME_DEFAULT) -> list[float]:
    """Compute one perplexity per sentence; empty list if no usable text."""
    from .features import split_sentences

    sentences = [s for s in split_sentences(text) if len(s.split()) >= 3]
    if not sentences:
        return []

    tok, model, torch = _load_model(model_name)
    ppls: list[float] = []
    for s in sentences:
        try:
            ids = tok(s, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                out = model(**ids, labels=ids["input_ids"])
            loss = float(out.loss.item())
            if math.isnan(loss) or math.isinf(loss):
                continue
            ppls.append(math.exp(loss))
        except Exception as exc:
            logger.debug("perplexity.sentence_skipped", error=str(exc))
            continue
    return ppls


def mean_perplexity(text: str, model_name: str = MODEL_NAME_DEFAULT) -> tuple[float, float]:
    """
    Return (mean_perplexity, std_perplexity) across sentences.

    Returns neutral defaults if no sentences could be scored.
    """
    text = _ensure_str(text)
    ppls = _sentence_perplexities(text, model_name)
    if not ppls:
        return 50.0, 10.0
    return float(np.mean(ppls)), float(np.std(ppls))


__all__ = ["MODEL_NAME_DEFAULT", "mean_perplexity"]
