"""
Health-check router.

GET /healthz   - liveness probe (always 200 if the process is up)
GET /readyz    - readiness probe (200 once critical subsystems are warm)
"""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is up."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz(request: Request) -> dict[str, object]:
    """
    Readiness probe — returns 200 once the app is initialised.

    Future: also check DB connectivity, ML model loads, and disk space.
    """
    app_state = getattr(request.app.state, "ready", False)
    return {
        "ready": bool(app_state),
        "service": "plagiarism-detected",
    }
