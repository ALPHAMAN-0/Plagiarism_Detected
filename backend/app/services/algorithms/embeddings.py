"""
Sentence-Transformer embeddings + cosine similarity.

Uses ``all-MiniLM-L6-v2`` (384-d) by default. We L2-normalise at encode time
so that a dot product equals cosine similarity.

The model is loaded lazily on first use and cached for the process.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from .base import Match
from .jaccard import _shorten

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _get_model(name: str) -> SentenceTransformer:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name)


_load_lock = threading.Lock()


def get_model(name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    """Thread-safe lazy loader for the embedding model."""
    if _get_model.cache_info().hits == 0 and _get_model.cache_info().currsize == 0:
        with _load_lock:
            return _get_model(name)
    return _get_model(name)


def _encode(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    """Encode a batch of texts and L2-normalise so dot == cosine."""
    vecs = model.encode(
        texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
    )
    return vecs.astype(np.float32, copy=False)


class EmbeddingAlgo:
    """Sentence-transformer embeddings + cosine similarity."""

    name = "embeddings"

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._corpus_vecs: np.ndarray | None = None
        self._corpus_snippets: list[str] = []

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = get_model(self.model_name)
        return self._model

    def fit(self, corpus_chunks: list[str]) -> None:
        model = self._ensure_model()
        if corpus_chunks:
            self._corpus_vecs = _encode(corpus_chunks, model)
        else:
            self._corpus_vecs = np.zeros((0, 384), dtype=np.float32)
        self._corpus_snippets = list(corpus_chunks)

    def score(self, query_chunks: list[str], top_k: int = 5, threshold: float = 0.0) -> list[Match]:
        if not query_chunks or self._corpus_vecs is None or self._corpus_vecs.shape[0] == 0:
            return []
        model = self._ensure_model()
        qv = _encode(query_chunks, model)
        sims = qv @ self._corpus_vecs.T  # (q, c), dot == cosine
        out: list[Match] = []
        for qi in range(sims.shape[0]):
            order = np.argsort(-sims[qi])[:top_k]
            for j in order:
                s = float(sims[qi, j])
                if s < threshold:
                    break
                out.append(
                    Match(
                        source_ref=int(j),
                        similarity=s,
                        snippet=_shorten(self._corpus_snippets[int(j)]),
                        chunk_index=qi,
                    )
                )
        return out


__all__ = ["EmbeddingAlgo", "get_model"]
