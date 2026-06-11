from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/health/")
async def health_check(request: Request) -> dict[str, str]:
    """Return the current service readiness state."""
    ready = bool(getattr(request.app.state, "ready", False))
    return {
        "status": "ok" if ready else "starting",
        "service": request.app.state.settings.APP_NAME,
        "version": request.app.state.settings.SERVICE_VERSION,
    }


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, bool | str]:
    """Return readiness and database status for orchestration checks."""
    ready = bool(getattr(request.app.state, "ready", False))
    return {
        "status": "ready" if ready else "starting",
        "ready": ready,
        "database": "ok" if ready else "starting",
    }
