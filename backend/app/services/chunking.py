"""
Text chunking — sentence-aware splitting suitable for downstream NLP.

Goal: produce chunks of ~target_size words while preserving sentence
boundaries. Used to feed the similarity algorithms and the AI detector.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")


def split_sentences(text: str) -> list[str]:
    """
    Split ``text`` into a list of sentences.

    Strategy: collapse whitespace, then break on terminal punctuation
    followed by whitespace + capital letter / quote / bracket. Short,
    deterministic, and good enough for English prose at MVP.

    Empty input returns an empty list. Input with no terminal punctuation
    is returned as a single element.
    """
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    parts = _SENTENCE_END.split(cleaned)
    return [s.strip() for s in parts if s.strip()]


def _word_chunks(text: str, size: int) -> Iterator[str]:
    """Yield chunks of `size` words (last may be shorter)."""
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i : i + size])


def chunk_text(
    text: str,
    target_size: int = 200,
    max_size: int = 400,
    overlap: int = 1,
) -> list[str]:
    """
    Greedy sentence-aware chunker.

    Args:
        text: input document.
        target_size: soft cap on words per chunk.
        max_size: hard cap on words per chunk (forces a split).
        overlap: number of trailing sentences to prepend to the next chunk.

    Returns:
        List of non-empty chunk strings.
    """
    sentences = split_sentences(text)
    # Fall back to word-level chunks when the text has no sentence boundaries
    if not sentences or (len(sentences) == 1 and len(sentences[0].split()) >= max_size):
        return [c for c in _word_chunks(text, max_size) if c.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        words = sent.split()
        wlen = len(words)
        # If a single sentence exceeds max_size, emit it on its own.
        if wlen >= max_size and not current:
            chunks.extend(_word_chunks(sent, max_size))
            continue
        # If adding this sentence would exceed max_size, flush current.
        if current and current_len + wlen > max_size:
            chunks.append(" ".join(current))
            overlap_sents = current[-overlap:] if overlap > 0 else []
            current = list(overlap_sents)
            current_len = sum(len(s.split()) for s in current)
        current.append(sent)
        current_len += wlen

    if current:
        chunks.append(" ".join(current))
    return [c for c in chunks if c.strip()]


__all__ = ["split_sentences", "chunk_text"]
