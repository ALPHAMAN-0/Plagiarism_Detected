"""
In-memory vector index for the corpus.

We keep this simple: a numpy matrix of L2-normalised embedding vectors plus a
parallel list of corpus source IDs. Persisted to a single .npz per corpus
under ``data/indexes/``.

This is intentionally not FAISS — at MVP scale (≤ 10k documents) numpy
top-k via argsort is fast enough and avoids a heavyweight dependency.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .security import safe_join


@dataclass
class IndexEntry:
    """A single chunk indexed in the corpus."""

    source_id: int
    text: str
    vector: np.ndarray  # (D,) float32, L2-normalised


@dataclass
class VectorIndex:
    """Holds the embedding matrix + metadata for a corpus."""

    name: str
    entries: list[IndexEntry] = field(default_factory=list)
    vectors: np.ndarray | None = None  # (N, D)

    def add(self, source_id: int, text: str, vector: np.ndarray) -> None:
        v = vector.astype(np.float32, copy=False)
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        self.entries.append(IndexEntry(source_id=source_id, text=text, vector=v))
        self.vectors = None  # invalidate cached matrix

    def _ensure_matrix(self) -> np.ndarray:
        if self.vectors is None and self.entries:
            self.vectors = np.stack([e.vector for e in self.entries], axis=0)
        return self.vectors if self.vectors is not None else np.zeros((0, 0), dtype=np.float32)

    def top_k(self, query_vec: np.ndarray, k: int = 5) -> list[tuple[int, float]]:
        """Return list of (index, cosine_similarity) for the top-k matches."""
        m = self._ensure_matrix()
        if m.size == 0:
            return []
        v = query_vec.astype(np.float32, copy=False)
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        sims = m @ v
        order = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in order]

    def save(self, indexes_dir: Path) -> Path:
        """Persist the index to disk; returns the path written."""
        path = safe_join(indexes_dir, f"{self.name}.npz")
        m = self._ensure_matrix()
        np.savez_compressed(
            path,
            vectors=m if m.size else np.zeros((0, 1), dtype=np.float32),
            metadata=np.array(
                json.dumps([{"source_id": e.source_id, "text": e.text} for e in self.entries])
            ),
        )
        return path

    @classmethod
    def load(cls, name: str, indexes_dir: Path) -> VectorIndex:
        path = safe_join(indexes_dir, f"{name}.npz")
        idx = cls(name=name)
        if not path.exists():
            return idx
        with np.load(path, allow_pickle=True) as data:
            meta = json.loads(str(data["metadata"]))
            idx.entries = [IndexEntry(**m, vector=np.zeros(0, dtype=np.float32)) for m in meta]
            vecs = data["vectors"]
            if vecs.size:
                idx.vectors = vecs
                # Re-attach vectors to entries
                for i, e in enumerate(idx.entries):
                    e.vector = vecs[i]
        return idx
