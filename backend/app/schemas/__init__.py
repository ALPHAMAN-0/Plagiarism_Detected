"""Pydantic v2 schemas for the public API."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    """Base for request/response models — reject unknown fields."""
    model_config = ConfigDict(extra="forbid")


# ----- documents -----

class DocumentUploadResponse(_Strict):
    document_id: str
    filename: str
    sha256: str
    size: int
    text_length: int
    chunks: int


# ----- corpus -----

class CorpusAddRequest(_Strict):
    document_id: str
    name: str = Field(min_length=1, max_length=120)


class CorpusAddResponse(_Strict):
    corpus_id: str
    name: str
    chunks: int


# ----- detect -----

class DetectRequest(_Strict):
    document_id: str
    algorithm: Literal["jaccard", "tfidf", "embeddings", "winnowing"] = "jaccard"
    top_k: int = Field(default=5, ge=1, le=50)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class ReportMatchOut(_Strict):
    chunk_index: int
    source_ref: int
    similarity: float
    snippet: str


class DetectResponse(_Strict):
    document_id: str
    algorithm: str
    matches: list[ReportMatchOut]
    summary: dict[str, float]


# ----- predict -----

class PredictRequest(_Strict):
    document_id: str


class PredictResponse(_Strict):
    document_id: str
    label: Literal["human", "ai", "plagiarised"]
    probabilities: dict[str, float]
    features: dict[str, float]
    model_version: str
