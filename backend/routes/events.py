from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from backend.models.alert import Alert
from backend.models.event import Event
from backend.schemas.alert import AlertIn, AlertOut
from backend.schemas.common import MessageResponse
from backend.schemas.event import EventIn
from backend.services.alerts import create_alert
from backend.services.events import create_event

router = APIRouter(prefix="/api/v1", tags=["events"])
_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

def _fan_out(alert: dict[str, Any]) -> None:
    """Publish an alert dictionary to all connected SSE subscribers."""
    for queue in list(_subscribers):
        queue.put_nowait(alert)


@router.post("/events", response_model=MessageResponse)
async def ingest_event(event: EventIn, request: Request) -> MessageResponse:
    """Persist a detection event from the P1 pipeline."""
    async with request.app.state.sessionmaker() as session:
        session.info["settings"] = request.app.state.settings
        await create_event(session, event)
    return MessageResponse(message="event stored")


@router.post("/alerts", response_model=MessageResponse)
async def ingest_alert(alert: AlertIn, request: Request) -> MessageResponse:
    """Persist an analytics alert from the P2 pipeline and notify SSE clients."""
    async with request.app.state.sessionmaker() as session:
        session.info["settings"] = request.app.state.settings
        if alert.event_id is None:
            frame_id = getattr(alert.metadata, "frame_id", None)
            if frame_id is not None:
                matched_result = await session.execute(
                    select(Event).where(Event.frame_id == int(frame_id)).order_by(Event.timestamp.desc()).limit(1)
                )
                matched_event = matched_result.scalar_one_or_none()
                if matched_event is not None:
                    alert = alert.model_copy(update={"event_id": matched_event.event_id})
        if alert.alert_id is not None:
            existing_result = await session.execute(select(Alert).where(Alert.alert_id == alert.alert_id))
            existing = existing_result.scalar_one_or_none()
            if existing is not None:
                return MessageResponse(message="duplicate")

        await session.rollback()
        alert_row = await create_alert(session, alert)
        alert_dict = {
            "id": getattr(alert_row, "id", 0) or 0,
            "alert_id": str(alert_row.alert_id),
            "alert_type": alert_row.alert_type,
            "severity": alert_row.severity,
            "object_id": alert_row.object_id,
            "class_name": alert_row.class_name,
            "zone": alert_row.zone,
            "clip_path": alert_row.clip_path,
            "metadata": alert_row.metadata_json,
            "timestamp": alert_row.timestamp.isoformat(),
            "created_at": alert_row.created_at.isoformat(),
        }

    _fan_out(alert_dict)
    return MessageResponse(message="alert stored")


@router.post("/frame", response_model=MessageResponse)
async def ingest_frame(request: Request, frame: UploadFile = File(..., alias="frame")) -> MessageResponse:
    """Accept and discard a frame upload from the P1 pipeline."""
    _ = request
    await frame.read()
    return MessageResponse(message="frame received")


@router.get("/alerts", response_model=list[AlertOut])
async def read_alerts(
    request: Request,
    alert_type: str | None = None,
    severity: str | None = None,
    zone: str | None = None,
    limit: int = 100,
) -> list[AlertOut]:
    """Return stored alerts with optional filtering."""
    query = select(Alert)
    if alert_type is not None:
        query = query.where(Alert.alert_type == alert_type)
    if severity is not None:
        query = query.where(Alert.severity == severity)
    if zone is not None:
        query = query.where(Alert.zone == zone)
    query = query.order_by(Alert.created_at.desc()).limit(min(limit, 500))

    async with request.app.state.sessionmaker() as session:
        result = await session.execute(query)
        rows = result.scalars().all()
    return [AlertOut.model_validate(row) for row in rows]


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def read_alert(alert_id: str, request: Request) -> AlertOut:
    """Return a single alert by its UUID string."""
    async with request.app.state.sessionmaker() as session:
        result = await session.execute(select(Alert).where(Alert.alert_id == alert_id))
        alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertOut.model_validate(alert)


@router.get("/incidents", response_model=list[AlertOut])
async def read_incidents(
    request: Request,
    alert_type: str | None = None,
    severity: str | None = None,
    zone: str | None = None,
    limit: int = 100,
) -> list[AlertOut]:
    """Return incident records as an alias of alerts."""
    return await read_alerts(request=request, alert_type=alert_type, severity=severity, zone=zone, limit=limit)


@router.get("/incidents/{alert_id}", response_model=AlertOut)
async def read_incident(alert_id: str, request: Request) -> AlertOut:
    """Return a single incident as an alias of an alert."""
    return await read_alert(alert_id=alert_id, request=request)


@router.get("/stream")
async def alert_stream(request: Request) -> StreamingResponse:
    """Stream newly ingested alerts to browser clients using SSE."""
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    _subscribers.add(queue)

    async def generator():
        try:
            while not await request.is_disconnected():
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(alert)}\n\n"
                except asyncio.TimeoutError:
                    yield "data: ping\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            _subscribers.discard(queue)

    return StreamingResponse(generator(), media_type="text/event-stream")
