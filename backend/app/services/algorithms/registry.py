"""
Algorithm registry — single dispatch point for similarity algorithms.

Adding a new algorithm = one line here + one module under ``algorithms/``.
"""

from __future__ import annotations

from typing import Final

from .base import Match, SimilarityAlgo
from .embeddings import EmbeddingAlgo
from .jaccard import JaccardAlgo
from .tfidf import TfidfAlgo
from .winnowing import WinnowingAlgo

__all__ = ["ALGOS", "get_algo", "UnknownAlgorithmError", "Match", "SimilarityAlgo"]


class UnknownAlgorithmError(KeyError):
    """Raised when an unregistered algorithm is requested."""


_ALGO_FACTORIES: Final[dict[str, type]] = {
    "jaccard": JaccardAlgo,
    "tfidf": TfidfAlgo,
    "embeddings": EmbeddingAlgo,
    "winnowing": WinnowingAlgo,
}


def get_algo(name: str) -> SimilarityAlgo:
    """Return a fresh instance of the named algorithm."""
    if name not in _ALGO_FACTORIES:
        raise UnknownAlgorithmError(
            f"Unknown algorithm {name!r}. Available: {sorted(_ALGO_FACTORIES)}"
        )
    return _ALGO_FACTORIES[name]()


# Public mapping (instances are created lazily — see ``get_algo``).
ALGOS: Final[dict[str, SimilarityAlgo]] = _ALGO_FACTORIES  # type: ignore[assignment]