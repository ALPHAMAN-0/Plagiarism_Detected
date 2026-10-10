"""RED tests for chunking service."""

from __future__ import annotations

from app.services.chunking import chunk_text, split_sentences


def test_split_sentences_simple() -> None:
    text = "Hello world. How are you? I am fine!"
    out = split_sentences(text)
    assert out == ["Hello world.", "How are you?", "I am fine!"]


def test_split_sentences_empty() -> None:
    assert split_sentences("") == []
    assert split_sentences("   \n\t  ") == []


def test_split_sentences_collapses_whitespace() -> None:
    text = "First  sentence.\n\nSecond   sentence."
    out = split_sentences(text)
    assert out == ["First sentence.", "Second sentence."]


def test_chunk_text_short_doc_single_chunk() -> None:
    text = "Sentence one. Sentence two. Sentence three."
    chunks = chunk_text(text, target_size=50)
    assert len(chunks) == 1
    assert "Sentence one" in chunks[0]
    assert "Sentence three" in chunks[0]


def test_chunk_text_long_doc_produces_multiple_chunks() -> None:
    # 100 sentences x 3 words each = 300 words
    text = " ".join(f"Sentence number {i} here." for i in range(100))
    chunks = chunk_text(text, target_size=40, max_size=80, overlap=0)
    assert len(chunks) > 1
    # Every chunk should be a substring of the original
    for c in chunks:
        assert all(tok in text for tok in c.split())


def test_chunk_text_respects_max_size() -> None:
    text = " ".join(f"Word{i}" for i in range(1000))
    chunks = chunk_text(text, target_size=100, max_size=200, overlap=0)
    for c in chunks:
        assert len(c.split()) <= 200
