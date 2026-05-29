from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from backend.models import Alert, Clip, Event
from backend.schemas.alert import AlertIn, AlertOut
from backend.schemas.common import MessageResponse
from backend.schemas.event import EventIn

router = APIRouter(prefix="/api/v1", tags=["events"])
_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO8601 timestamp and normalize it to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fan_out(alert: dict[str, Any]) -> None:
    """Publish an alert dictionary to all connected SSE subscribers."""
    for queue in list(_subscribers):
        queue.put_nowait(alert)


@router.post("/events", response_model=MessageResponse)
async def ingest_event(event: EventIn, request: Request) -> MessageResponse:
    """Persist a detection event from the P1 pipeline."""
    async with request.app.state.sessionmaker() as session:
        session.add(
            Event(
                frame_id=event.frame_id,
                timestamp=_parse_datetime(event.timestamp),
                object_count=len(event.objects),
                raw_json=event.model_dump_json(),
            )
        )
        await session.commit()
    return MessageResponse(message="ok")


@router.post("/alerts", response_model=MessageResponse)
async def ingest_alert(alert: AlertIn, request: Request) -> MessageResponse:
    """Persist an analytics alert from the P2 pipeline and notify SSE clients."""
    async with request.app.state.sessionmaker() as session:
        existing = await session.scalar(select(Alert).where(Alert.alert_id == alert.alert_id))
        if existing is not None:
            return MessageResponse(message="duplicate")

        timestamp = _parse_datetime(alert.timestamp)
        metadata = alert.metadata.model_dump()
        alert_row = Alert(
            alert_id=alert.alert_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            object_id=alert.object_id,
            class_name=alert.class_name,
            zone=alert.zone,
            metadata_json=json.dumps(metadata),
            clip_path=alert.clip_path,
            timestamp=timestamp,
        )
        session.add(alert_row)
        if alert.clip_path:
            session.add(Clip(alert_id=alert.alert_id, file_path=alert.clip_path, duration_seconds=None))
        await session.commit()
        await session.refresh(alert_row)

        alert_dict = {
            "id": alert_row.id,
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "object_id": alert.object_id,
            "class_name": alert.class_name,
            "zone": alert.zone,
            "clip_path": alert.clip_path,
            "metadata": metadata,
            "timestamp": timestamp.isoformat(),
            "created_at": alert_row.created_at.isoformat(),
        }

    _fan_out(alert_dict)
    return MessageResponse(message="ok")


@router.post("/frame", response_model=MessageResponse)
async def ingest_frame(request: Request, file: UploadFile = File(...)) -> MessageResponse:
    """Accept and discard a frame upload from the P1 pipeline."""
    _ = request
    await file.read()
    return MessageResponse(message="ok")


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
    query = query.order_by(Alert.timestamp.desc()).limit(min(limit, 500))

    async with request.app.state.sessionmaker() as session:
        rows = (await session.scalars(query)).all()
    return [AlertOut.model_validate(row) for row in rows]


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def read_alert(alert_id: str, request: Request) -> AlertOut:
    """Return a single alert by its UUID string."""
    async with request.app.state.sessionmaker() as session:
        alert = await session.scalar(select(Alert).where(Alert.alert_id == alert_id))
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
