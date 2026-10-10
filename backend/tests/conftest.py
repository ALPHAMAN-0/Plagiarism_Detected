"""
Shared pytest fixtures.

Every test gets an isolated, in-process FastAPI app backed by a temporary
SQLite DB. No network. No global state.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_data_dir(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Provide a clean, temporary data directory for the duration of a test."""
    tmpdir = Path(tempfile.mkdtemp(prefix="plagiarism_test_"))
    (tmpdir / "uploads").mkdir()
    (tmpdir / "indexes").mkdir()
    monkeypatch.setenv("UPLOADS_DIR", str(tmpdir / "uploads"))
    monkeypatch.setenv("INDEXES_DIR", str(tmpdir / "indexes"))
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmpdir / 'test.db'}")
    monkeypatch.setenv("ML_MODELS_DIR", str(tmpdir / "ml_models"))
    (tmpdir / "ml_models").mkdir()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def client(tmp_data_dir: Path) -> Iterator[TestClient]:
    """FastAPI test client with isolated config."""
    # Import inside the fixture so env vars are set first
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
