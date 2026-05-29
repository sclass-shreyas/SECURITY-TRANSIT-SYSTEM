from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from backend.schemas.common import HealthResponse, ReadyResponse
from backend.services.health import database_is_ready

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.SERVICE_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", response_model=ReadyResponse)
async def ready(request: Request) -> ReadyResponse:
    if not request.app.state.ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not ready")

    sessionmaker = request.app.state.sessionmaker
    db_ready = await database_is_ready(sessionmaker)
    if not db_ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")

    return ReadyResponse(status="ready", ready=True, database="ok")
