from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from backend.models.analytics_result import AnalyticsResult
from backend.schemas.analytics_result import AnalyticsResultIn, AnalyticsResultOut
from backend.schemas.common import MessageResponse
from backend.services.analytics_results import record_analytics_result

router = APIRouter(prefix="/api/v1/analytics-results", tags=["analytics-results"])


@router.post("/", response_model=MessageResponse)
async def ingest_analytics_result(payload: AnalyticsResultIn, request: Request) -> MessageResponse:
    """Persist a detector output tied to a source event."""
    async with request.app.state.sessionmaker() as session:
        session.info["settings"] = request.app.state.settings
        await record_analytics_result(session, payload)
    return MessageResponse(message="analytics result stored")


@router.post("", response_model=MessageResponse)
async def ingest_analytics_result_no_slash(payload: AnalyticsResultIn, request: Request) -> MessageResponse:
    """Persist a detector output tied to a source event."""
    return await ingest_analytics_result(payload, request)


@router.get("/", response_model=list[AnalyticsResultOut])
async def list_analytics_results(request: Request, event_id: str | None = None) -> list[AnalyticsResultOut]:
    """List analytics results, optionally filtered by source event."""
    query = select(AnalyticsResult).order_by(AnalyticsResult.created_at.desc())
    if event_id is not None:
        query = query.where(AnalyticsResult.event_id == event_id)

    async with request.app.state.sessionmaker() as session:
        result = await session.execute(query)
        rows = result.scalars().all()
    return [AnalyticsResultOut.model_validate(row) for row in rows]


@router.get("", response_model=list[AnalyticsResultOut])
async def list_analytics_results_no_slash(request: Request, event_id: str | None = None) -> list[AnalyticsResultOut]:
    """List analytics results, optionally filtered by source event."""
    return await list_analytics_results(request, event_id)


@router.get("/{result_id}", response_model=AnalyticsResultOut)
async def get_analytics_result(result_id: str, request: Request) -> AnalyticsResultOut:
    """Return one analytics result by ID."""
    async with request.app.state.sessionmaker() as session:
        result = await session.execute(select(AnalyticsResult).where(AnalyticsResult.result_id == result_id))
        row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analytics result not found")
    return AnalyticsResultOut.model_validate(row)
