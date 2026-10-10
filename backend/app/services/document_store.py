"""
In-process document + corpus store.

For the MVP we keep state in memory keyed by UUID. A real deployment would
back this with SQLite or Postgres; the storage interface stays the same.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field


@dataclass
class StoredDocument:
    document_id: str
    filename: str
    text: str
    sha256: str
    size: int


@dataclass
class CorpusEntry:
    corpus_id: str
    name: str
    chunks: list[str] = field(default_factory=list)


class DocumentStore:
    """Thread-safe in-memory store."""

    def __init__(self) -> None:
        self._docs: dict[str, StoredDocument] = {}
        self._corphora: dict[str, CorpusEntry] = {}
        self._lock = threading.Lock()

    # ----- documents -----

    def add_document(self, filename: str, text: str, sha256: str, size: int) -> StoredDocument:
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        doc = StoredDocument(
            document_id=doc_id,
            filename=filename,
            text=text,
            sha256=sha256,
            size=size,
        )
        with self._lock:
            self._docs[doc_id] = doc
        return doc

    def get_document(self, document_id: str) -> StoredDocument | None:
        return self._docs.get(document_id)

    # ----- corpus -----

    def add_corpus(self, name: str, chunks: list[str]) -> CorpusEntry:
        corpus_id = f"corpus_{uuid.uuid4().hex[:12]}"
        entry = CorpusEntry(corpus_id=corpus_id, name=name, chunks=list(chunks))
        with self._lock:
            self._corphora[corpus_id] = entry
        return entry

    def get_corpus(self, corpus_id: str) -> CorpusEntry | None:
        return self._corphora.get(corpus_id)

    def list_corpora(self) -> list[CorpusEntry]:
        return list(self._corphora.values())

    def all_corpus_chunks(self) -> list[str]:
        out: list[str] = []
        for c in self._corphora.values():
            out.extend(c.chunks)
        return out


# Module-level singleton
_store: DocumentStore | None = None


def get_store() -> DocumentStore:
    """Return the process-wide document store."""
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store


def reset_store() -> None:
    """Drop the singleton so a fresh one is created on next call. Tests only."""
    global _store
    _store = None
