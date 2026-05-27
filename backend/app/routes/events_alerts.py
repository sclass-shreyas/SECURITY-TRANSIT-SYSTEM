from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.clip import Clip
from app.models.event import Event
from app.models.user import User
from app.schemas.alert import AlertIn, AlertOut
from app.schemas.common import MessageResponse
from app.schemas.event import EventIn
from app.websocket.manager import ws_manager

router = APIRouter(tags=["events-alerts"])


def to_alert_out(alert: Alert) -> AlertOut:
    return AlertOut(
        alert_id=alert.alert_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        timestamp=alert.timestamp,
        object_id=alert.object_id,
        class_name=alert.class_name,
        zone=alert.zone,
        clip_path=alert.clip_path,
        metadata=alert.metadata_json,
    )


async def query_alerts(db: AsyncSession, severity: str | None, limit: int) -> list[AlertOut]:
    query = select(Alert)
    if severity:
        query = query.where(Alert.severity == severity)
    query = query.order_by(desc(Alert.timestamp)).limit(limit)
    result = await db.execute(query)
    return [to_alert_out(alert) for alert in result.scalars().all()]


@router.post("/events", response_model=MessageResponse)
async def create_event(payload: EventIn, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    event = Event(
        frame_id=payload.frame_id,
        timestamp=payload.timestamp,
        raw_json=payload.model_dump(mode="json"),
    )
    db.add(event)
    await db.commit()
    await ws_manager.broadcast(
        {"type": "event", "timestamp": datetime.now(timezone.utc), "payload": payload.model_dump(mode="json")}
    )
    return MessageResponse(message="event stored")


@router.post("/alerts", response_model=MessageResponse)
async def create_alert(payload: AlertIn, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    alert = Alert(
        alert_id=payload.alert_id,
        alert_type=payload.alert_type,
        severity=payload.severity,
        timestamp=payload.timestamp,
        object_id=payload.object_id,
        class_name=payload.class_name,
        zone=payload.zone,
        clip_path=payload.clip_path,
        metadata_json=payload.metadata,
    )
    db.add(alert)
    if payload.clip_path:
        db.add(Clip(alert_id=payload.alert_id, clip_path=payload.clip_path))
    await db.commit()
    alert_dump = payload.model_dump(mode="json")
    await ws_manager.broadcast({"type": "alert", "timestamp": datetime.now(timezone.utc), "payload": alert_dump})
    await ws_manager.broadcast({"type": "incident_update", "timestamp": datetime.now(timezone.utc), "payload": alert_dump})
    return MessageResponse(message="alert stored")


@router.post("/frame", response_model=MessageResponse)
async def ingest_frame(frame: UploadFile = File(...)) -> MessageResponse:
    content = await frame.read()
    await ws_manager.broadcast(
        {
            "type": "frame",
            "timestamp": datetime.now(timezone.utc),
            "payload": {"filename": frame.filename, "content_type": frame.content_type, "size": len(content)},
        }
    )
    return MessageResponse(message="frame received")


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[AlertOut]:
    return await query_alerts(db=db, severity=severity, limit=limit)


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> AlertOut:
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return to_alert_out(alert)


@router.get("/incidents", response_model=list[AlertOut])
async def list_incidents(
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[AlertOut]:
    return await query_alerts(db=db, severity=severity, limit=limit)


@router.get("/incidents/{alert_id}", response_model=AlertOut)
async def get_incident(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> AlertOut:
    return await get_alert(alert_id=alert_id, db=db, _user=_user)
