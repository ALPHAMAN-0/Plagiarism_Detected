"""Integration tests for the end-to-end API flow."""

from __future__ import annotations

import io


def _upload(client, content: bytes, filename: str = "doc.txt") -> str:
    files = {"file": (filename, io.BytesIO(content), "text/plain")}
    r = client.post("/api/v1/documents", files=files)
    assert r.status_code == 201, r.text
    return r.json()["document_id"]


def test_upload_then_corpus_then_detect_flow(client) -> None:
    # 1. Upload a document
    doc_id = _upload(client, b"This is a test document with some text content. " * 5)
    assert doc_id.startswith("doc_")

    # 2. Add to corpus
    r = client.post(
        "/api/v1/corpus",
        json={"document_id": doc_id, "name": "test_corpus"},
    )
    assert r.status_code == 201, r.text
    corpus = r.json()
    assert corpus["chunks"] >= 1

    # 3. Run detection
    r = client.post(
        "/api/v1/analyses/detect",
        json={
            "document_id": doc_id,
            "algorithm": "jaccard",
            "top_k": 3,
            "threshold": 0.0,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["algorithm"] == "jaccard"
    assert isinstance(body["matches"], list)
    assert "summary" in body
    assert "top_similarity" in body["summary"]


def test_detect_rejects_unknown_document(client) -> None:
    r = client.post(
        "/api/v1/analyses/detect",
        json={"document_id": "doc_does_not_exist", "algorithm": "jaccard"},
    )
    assert r.status_code == 404


def test_detect_rejects_unknown_algorithm(client) -> None:
    doc_id = _upload(client, b"hello world. some text here.")
    r = client.post(
        "/api/v1/analyses/detect",
        json={"document_id": doc_id, "algorithm": "moss"},
    )
    # Pydantic strict-mode → 422
    assert r.status_code == 422


def test_detect_rejects_when_corpus_empty(client) -> None:
    doc_id = _upload(client, b"hello world. some text here.")
    r = client.post(
        "/api/v1/analyses/detect",
        json={"document_id": doc_id, "algorithm": "jaccard"},
    )
    assert r.status_code == 409


def test_upload_rejects_oversized(client, tmp_data_dir) -> None:
    # 11 MB — over the 10 MB default cap
    big = b"x" * (11 * 1024 * 1024)
    files = {"file": ("big.txt", io.BytesIO(big), "text/plain")}
    r = client.post("/api/v1/documents", files=files)
    assert r.status_code == 413


def test_upload_rejects_path_traversal_filename(client) -> None:
    files = {"file": ("../../etc/passwd.txt", io.BytesIO(b"hi"), "text/plain")}
    r = client.post("/api/v1/documents", files=files)
    # safe_filename strips the prefix → final filename "passwd.txt" which IS valid
    # The header here is "no path-component in final filename"; test that name is sanitized
    assert r.status_code == 201
    body = r.json()
    assert body["filename"] == "passwd.txt"


def test_predict_returns_three_class_probabilities(client) -> None:
    doc_id = _upload(
        client,
        b"The quick brown fox jumps over the lazy dog. "
        b"It was a bright cold day in April, and the clocks were striking thirteen. " * 3,
    )
    r = client.post("/api/v1/predict", json={"document_id": doc_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] in {"human", "ai", "plagiarised"}
    assert set(body["probabilities"].keys()) == {"human", "ai", "plagiarised"}
    assert abs(sum(body["probabilities"].values()) - 1.0) < 1e-3
    assert isinstance(body["model_version"], str)
    assert "avg_sentence_length" in body["features"]
