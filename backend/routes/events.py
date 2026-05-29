from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.deps import get_db
from backend.schemas.alert import AlertIn, AlertOut
from backend.schemas.common import MessageResponse
from backend.schemas.event import EventIn
from backend.services.alerts import alert_to_out, create_alert, get_alert, list_alerts
from backend.services.events import create_event

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.post("/events", response_model=MessageResponse)
async def ingest_event(payload: EventIn, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await create_event(db, payload)
    return MessageResponse(message="event stored")


@router.post("/alerts", response_model=MessageResponse)
async def ingest_alert(payload: AlertIn, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await create_alert(db, payload)
    return MessageResponse(message="alert stored")


@router.post("/frame", response_model=MessageResponse)
async def ingest_frame(frame: UploadFile = File(...)) -> MessageResponse:
    content = await frame.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty frame payload")
    return MessageResponse(message="frame received")


@router.get("/alerts", response_model=list[AlertOut])
async def read_alerts(
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    return await list_alerts(db=db, severity=severity, limit=limit)


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def read_alert(alert_id: str, db: AsyncSession = Depends(get_db)) -> AlertOut:
    alert = await get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert_to_out(alert)


@router.get("/incidents", response_model=list[AlertOut])
async def read_incidents(
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    return await list_alerts(db=db, severity=severity, limit=limit)


@router.get("/incidents/{alert_id}", response_model=AlertOut)
async def read_incident(alert_id: str, db: AsyncSession = Depends(get_db)) -> AlertOut:
    return await read_alert(alert_id=alert_id, db=db)
