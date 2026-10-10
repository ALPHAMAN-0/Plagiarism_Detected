"""
Jaccard / n-gram shingling similarity.

Reference: classic shingling technique used in early web-duplicate detection.
Each chunk is reduced to a set of word-level n-grams; similarity between two
chunks is the Jaccard index of their shingle sets.

This is cheap, fully deterministic, and works well for detecting exact and
near-exact copies.
"""

from __future__ import annotations

import re

from .base import Match

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def shingle(text: str, n: int = 5) -> set[str]:
    """Return the set of word-level n-grams in ``text``."""
    tokens = _TOKEN_RE.findall((text or "").lower())
    if len(tokens) < n:
        # Short text → return the whole token list as a single shingle
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard index of two sets, in [0, 1]."""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


class JaccardAlgo:
    """n-gram Jaccard similarity."""

    name = "jaccard"

    def __init__(self, n: int = 5) -> None:
        self.n = n
        self._corpus_shingles: list[set[str]] = []
        self._corpus_snippets: list[str] = []

    def fit(self, corpus_chunks: list[str]) -> None:
        self._corpus_shingles = [shingle(c, self.n) for c in corpus_chunks]
        self._corpus_snippets = list(corpus_chunks)

    def score(
        self, query_chunks: list[str], top_k: int = 5, threshold: float = 0.0
    ) -> list[Match]:
        if not query_chunks or not self._corpus_shingles:
            return []
        out: list[Match] = []
        for qi, q in enumerate(query_chunks):
            qs = shingle(q, self.n)
            if not qs:
                continue
            scored = [
                (j, jaccard(qs, cs))
                for j, cs in enumerate(self._corpus_shingles)
                if cs
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            for j, s in scored[:top_k]:
                if s < threshold:
                    break
                out.append(
                    Match(
                        source_ref=j,
                        similarity=float(s),
                        snippet=_shorten(self._corpus_snippets[j]),
                        chunk_index=qi,
                    )
                )
        return out


def _shorten(text: str, limit: int = 240) -> str:
    """Truncate text for the report snippet."""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


__all__ = ["JaccardAlgo", "shingle", "jaccard"]