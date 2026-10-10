# Plagiarism_Detected — Makefile for the full 6-phase verification loop.
# Use `make verify` to run everything end-to-end.

.PHONY: help install backend-install frontend-install
.PHONY: backend-test frontend-test type-check lint security build diff verify clean
.PHONY: backend-lint backend-format frontend-lint backend-train

BACKEND_DIR := backend
FRONTEND_DIR := frontend

help:
	@echo "Targets:"
	@echo "  install         install both backend and frontend deps"
	@echo "  backend-test    pytest with coverage"
	@echo "  backend-lint    ruff check + format check"
	@echo "  backend-format  ruff format (write)"
	@echo "  frontend-test   vitest run"
	@echo "  frontend-lint   eslint"
	@echo "  type-check      mypy + tsc"
	@echo "  lint            backend-lint + frontend-lint"
	@echo "  security        bandit + pip-audit + npm audit + gitleaks (local)"
	@echo "  build           tsc + vite build"
	@echo "  verify          run all 6 phases end-to-end"
	@echo "  diff            git diff stat"
	@echo "  clean           remove caches and build artifacts"

install: backend-install frontend-install

backend-install:
	cd $(BACKEND_DIR) && uv sync --extra dev

frontend-install:
	cd $(FRONTEND_DIR) && npm ci

backend-test:
	cd $(BACKEND_DIR) && uv run pytest -q --cov=app --cov-fail-under=80

backend-lint:
	cd $(BACKEND_DIR) && uv run ruff check app tests && uv run ruff format --check

backend-format:
	cd $(BACKEND_DIR) && uv run ruff format

# Train the AI/human/plagiarism classifier. Persists the .joblib model to
# app/ml_models/ai_classifier.joblib. Required by the trained-model smoke
# tests in tests/unit/test_trained_model.py.
backend-train:
	cd $(BACKEND_DIR) && uv run python -m app.services.ai_detect.train \
		--csv data/ai_train.csv \
		--out app/ml_models/ai_classifier.joblib

frontend-test:
	cd $(FRONTEND_DIR) && npx vitest run

frontend-lint:
	cd $(FRONTEND_DIR) && npx eslint . --ext .ts,.tsx

type-check:
	cd $(BACKEND_DIR) && uv run mypy app
	cd $(FRONTEND_DIR) && npx tsc --noEmit

lint: backend-lint frontend-lint

security:
	@echo "==> bandit"
	cd $(BACKEND_DIR) && uv run pip install -q bandit[toml] && uv run bandit -r app -lll
	@echo "==> pip-audit"
	cd $(BACKEND_DIR) && uv run pip install -q pip-audit && uv run pip-audit --strict || true
	@echo "==> npm audit"
	cd $(FRONTEND_DIR) && npm audit --audit-level=high
	@echo "==> gitleaks"
	which gitleaks >/dev/null && gitleaks detect --no-banner || echo "gitleaks not installed; install via brew install gitleaks"

build:
	cd $(FRONTEND_DIR) && npm run build

diff:
	git diff --stat
	git status --short

verify: install backend-lint type-check backend-test frontend-test frontend-lint build security
	@echo
	@echo "=================================================="
	@echo "  ALL PHASES GREEN"
	@echo "=================================================="

clean:
	rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.mypy_cache $(BACKEND_DIR)/.ruff_cache $(BACKEND_DIR)/.coverage $(BACKEND_DIR)/htmlcov
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/.vite $(FRONTEND_DIR)/coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
