"""
TF-IDF + cosine similarity.

We use scikit-learn's TfidfVectorizer with unigrams + bigrams and standard
pre-tokenised input (our own tokenisation). At fit time we build a sparse
matrix over the corpus; at score time we transform the query and use argsort
to take the top-k matches per chunk.

Algorithm: ``cosine_similarity(query_matrix, corpus_matrix).T`` gives a
(corpus, query) similarity matrix; per query column, argsort descending.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base import Match
from .jaccard import _shorten

_TOKEN_RE = __import__("re").compile(r"\w+", __import__("re").UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


class TfidfAlgo:
    """TF-IDF (1-2 grams) + cosine similarity."""

    name = "tfidf"

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._corpus_matrix = None
        self._corpus_snippets: list[str] = []

    def fit(self, corpus_chunks: list[str]) -> None:
        self._vectorizer = TfidfVectorizer(
            tokenizer=_tokenize,
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
            lowercase=False,  # already lowered by _tokenize
        )
        self._corpus_matrix = self._vectorizer.fit_transform(corpus_chunks)
        self._corpus_snippets = list(corpus_chunks)

    def score(self, query_chunks: list[str], top_k: int = 5, threshold: float = 0.0) -> list[Match]:
        if not query_chunks or self._vectorizer is None or self._corpus_matrix is None:
            return []
        qm = self._vectorizer.transform(query_chunks)
        sims = cosine_similarity(qm, self._corpus_matrix)  # (q, c) dense
        out: list[Match] = []
        for qi in range(sims.shape[0]):
            row = sims[qi]
            order = np.argsort(-row)[:top_k]
            for j in order:
                s = float(row[j])
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


__all__ = ["TfidfAlgo"]
