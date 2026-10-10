"""
Base protocol + dataclass for similarity algorithms.

Every algorithm exposes the same shape so the rest of the system can swap
implementations without special-casing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Match:
    """A single similarity match between a query chunk and a corpus chunk."""

    source_ref: int  # index into the corpus
    similarity: float  # in [0, 1]
    snippet: str  # short excerpt of the matched corpus chunk
    chunk_index: int = 0  # query-side chunk index (for UI highlighting)

    def __post_init__(self) -> None:
        # Clamp into [0, 1] — algorithms can occasionally overshoot due to
        # float math; downstream rendering assumes this range.
        if not 0.0 <= self.similarity <= 1.0:
            object.__setattr__(self, "similarity", min(1.0, max(0.0, self.similarity)))


@runtime_checkable
class SimilarityAlgo(Protocol):
    """Protocol every similarity algorithm implements."""

    name: str

    def fit(self, corpus_chunks: list[str]) -> None:
        """Index a corpus of reference chunks. Idempotent."""
        ...

    def score(self, query_chunks: list[str], top_k: int = 5, threshold: float = 0.0) -> list[Match]:
        """Return top-k matches for the given query chunks (filtered by threshold)."""
        ...


__all__ = ["Match", "SimilarityAlgo"]
