from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check(request: Request) -> dict[str, str]:
    """Return the current service readiness state."""
    return {
        "status": "ok" if request.app.state.ready else "starting",
        "service": "backend",
    }
