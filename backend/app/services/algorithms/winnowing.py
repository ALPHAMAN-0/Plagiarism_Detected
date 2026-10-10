"""
Winnowing — MOSS-style document fingerprinting.

Reference:
  Schleimer, Wilkerson, Aiken, "Winnowing: Local Algorithms for Document
  Fingerprinting" (SIGMOD 2003). Hashes k-grams to integers, then for every
  window of ``w`` consecutive hashes selects the *minimum* (rightmost on
  ties) as the fingerprint.

Similarity between two documents is the Jaccard index of their fingerprint
sets — fast even on very large texts.
"""

from __future__ import annotations

import hashlib
import re

from .base import Match
from .jaccard import _shorten, jaccard

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _hash_kgram(tokens: list[str], i: int, k: int) -> int:
    """Hash a k-gram starting at position ``i``."""
    gram = " ".join(tokens[i : i + k])
    # MD5 is the standard MOSS fingerprint hash; this is a non-crypto
    # use (text fingerprinting). `usedforsecurity=False` tells bandit/ruff
    # this is intentionally not a security-sensitive hash.
    h = hashlib.md5(gram.encode("utf-8"), usedforsecurity=False).digest()
    return int.from_bytes(h[:4], "big")


def winnow(tokens: list[str], k: int = 5, w: int = 4) -> list[int]:
    """
    Produce the list of fingerprints for a sequence of tokens.

    Args:
        tokens: tokenised document.
        k: k-gram size. The original MOSS paper uses k=25 for full papers,
           but Plagiarism_Detected typically scores paragraphs and essays
           (~50–500 tokens). Empirically (see
           tests/unit/test_algorithms.py::test_winnowing_*) k=5 gives
           near-copy overlap of ~0.85 vs ~0.17 for k=25 on a 62-token
           document with a one-word insertion.
        w: window size for selecting minima (default 4).

    Returns:
        List of integer fingerprints (left-to-right order).
    """
    if len(tokens) < k:
        # Fall back to hashing the whole token list
        return [_hash_kgram(tokens, 0, max(1, len(tokens)))] if tokens else []

    hashes = [_hash_kgram(tokens, i, k) for i in range(len(tokens) - k + 1)]

    # Per Schleimer-Wilkerson-Aiken (SIGMOD 2003): for each window of size w,
    # record the minimum hash. The original paper does NOT deduplicate the
    # fingerprint list — duplicates are dropped naturally when the list is
    # converted to a set for the Jaccard comparison. The previous
    # "if min_val != last_min" guard was not part of the paper and
    # collapsed the fingerprint set on small edits, which caused a single
    # word insertion in a near-copy to drop the Jaccard overlap from ~1.0
    # to ~0.2.
    fingerprints = [min(hashes[i : i + w]) for i in range(len(hashes) - w + 1)]
    return fingerprints


def _fingerprint_set(tokens: list[str], k: int, w: int) -> set[int]:
    return set(winnow(tokens, k, w))


class WinnowingAlgo:
    """MOSS-style winnowing similarity."""

    name = "winnowing"

    def __init__(self, k: int = 5, w: int = 4) -> None:
        self.k = k
        self.w = w
        self._corpus_fps: list[set[int]] = []
        self._corpus_snippets: list[str] = []

    def fit(self, corpus_chunks: list[str]) -> None:
        self._corpus_fps = [
            _fingerprint_set(_TOKEN_RE.findall(c.lower()), self.k, self.w) for c in corpus_chunks
        ]
        self._corpus_snippets = list(corpus_chunks)

    def score(self, query_chunks: list[str], top_k: int = 5, threshold: float = 0.0) -> list[Match]:
        if not query_chunks or not self._corpus_fps:
            return []
        out: list[Match] = []
        for qi, q in enumerate(query_chunks):
            qfp = _fingerprint_set(_TOKEN_RE.findall(q.lower()), self.k, self.w)
            if not qfp:
                continue
            scored = [
                (j, jaccard(qfp, cf))  # type: ignore[arg-type]
                for j, cf in enumerate(self._corpus_fps)
                if cf
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


__all__ = ["WinnowingAlgo", "winnow"]
