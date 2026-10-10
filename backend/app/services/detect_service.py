"""
Detect service — orchestrates the end-to-end plagiarism check.

Flow: chunk document → run selected algorithm against the registered corpus
chunks → build a sanitized report.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

from .algorithms.base import Match
from .algorithms.registry import get_algo
from .chunking import chunk_text
from .reporting import Report, build_report

logger = logging.getLogger(__name__)


def run_detection(
    document_text: str,
    corpus_chunks: Sequence[str],
    algorithm: str,
    top_k: int = 5,
    threshold: float = 0.0,
    target_chunk_size: int = 200,
) -> Report:
    """
    Run a plagiarism check.

    Args:
        document_text: full text of the document being checked.
        corpus_chunks: pre-chunked reference corpus.
        algorithm: one of "jaccard", "tfidf", "embeddings", "winnowing".
        top_k: maximum number of matches to return.
        threshold: drop matches below this similarity.
        target_chunk_size: words per chunk when splitting the query.

    Returns:
        A sanitized ``Report``.
    """
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    query_chunks = chunk_text(document_text, target_size=target_chunk_size)
    algo = get_algo(algorithm)
    algo.fit(list(corpus_chunks))
    matches: list[Match] = algo.score(query_chunks, top_k=top_k, threshold=threshold)
    logger.info(
        "detection.done algorithm=%s query_chunks=%d matches=%d",
        algorithm,
        len(query_chunks),
        len(matches),
    )
    return build_report(
        document_id=doc_id,
        algorithm=algorithm,
        matches=matches,
    )


__all__ = ["run_detection"]
