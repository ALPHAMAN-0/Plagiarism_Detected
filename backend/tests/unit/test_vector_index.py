"""Unit tests for the simple numpy-based vector index."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.services.vector_index import VectorIndex


def _vec(values: list[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float32)


def test_top_k_returns_matches_ordered_by_cosine() -> None:
    idx = VectorIndex(name="t")
    idx.add(source_id=1, text="hello", vector=_vec([1.0, 0.0, 0.0]))
    idx.add(source_id=2, text="goodbye", vector=_vec([0.0, 1.0, 0.0]))
    matches = idx.top_k(_vec([0.95, 0.05, 0.0]), k=2)
    # top_k returns (positional_index, score)
    assert matches[0][0] == 0  # first entry has highest cosine
    assert matches[0][1] > matches[1][1]


def test_empty_index_returns_empty_list() -> None:
    idx = VectorIndex(name="empty")
    assert idx.top_k(_vec([1.0, 0.0, 0.0])) == []


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    idx = VectorIndex(name="alpha")
    idx.add(source_id=42, text="persisted", vector=_vec([0.1, 0.2, 0.3]))
    path = idx.save(indexes_dir=tmp_path)
    assert path.exists()

    loaded = VectorIndex.load(name="alpha", indexes_dir=tmp_path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].source_id == 42
    assert loaded.entries[0].text == "persisted"
    matches = loaded.top_k(_vec([0.1, 0.2, 0.3]), k=1)
    assert matches and matches[0][1] > 0.99


def test_load_missing_file_returns_empty_index(tmp_path: Path) -> None:
    idx = VectorIndex.load(name="missing", indexes_dir=tmp_path)
    assert idx.entries == []


def test_add_normalises_vector() -> None:
    idx = VectorIndex(name="t")
    big = _vec([3.0, 4.0, 0.0])  # norm 5
    idx.add(source_id=1, text="x", vector=big)
    v = idx.entries[0].vector
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-5
