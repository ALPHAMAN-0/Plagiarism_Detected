"""
FastAPI application factory.

Wires up CORS, settings, structured logging, routers, and lifespan management.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import analyses, corpus, documents, health, predict


def _configure_logging(level: str) -> None:
    """Configure structlog + stdlib logging to share a JSON-friendly format."""
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Mark the app ready once startup is complete."""
    settings = get_settings()
    _configure_logging(settings.log_level)
    log = structlog.get_logger("plagiarism")
    log.info("startup", env=settings.app_env, version=settings.app_version)
    app.state.ready = True
    try:
        yield
    finally:
        app.state.ready = False
        log.info("shutdown")


def create_app() -> FastAPI:
    """Build a FastAPI app. Used by both the runtime entrypoint and tests."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=_lifespan,
        # Never leak tracebacks in response bodies.
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url=None,
    )

    # CORS — explicit allowlist (never "*" in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "Accept"],
        max_age=600,
    )

    # Global exception handler — sanitized error responses
    @app.exception_handler(Exception)
    async def _safe_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        log = structlog.get_logger("plagiarism")
        log.error("unhandled_exception", type=type(exc).__name__, msg=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "An unexpected error occurred."},
        )

    # Routers
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(corpus.router)
    app.include_router(analyses.router)
    app.include_router(predict.router)

    return app


# Module-level app for `uvicorn app.main:app` (development convenience)
app = create_app()
