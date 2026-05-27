from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.event import Event
from app.models.user import User
from app.schemas.stats import StatsSummary, TimelinePoint
from app.services.ingest_service import get_alert_counts_by_severity

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsSummary)
@router.get("/summary", response_model=StatsSummary)
async def stats_summary(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> StatsSummary:
    event_count = await db.scalar(select(func.count(Event.id)))
    alert_count = await db.scalar(select(func.count(Alert.alert_id)))
    by_severity = await get_alert_counts_by_severity(db)
    return StatsSummary(total_events=event_count or 0, total_alerts=alert_count or 0, alerts_by_severity=by_severity)


@router.get("/timeline", response_model=list[TimelinePoint])
async def stats_timeline(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TimelinePoint]:
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(6, -1, -1):
        bucket = (now.replace(minute=0, second=0, microsecond=0)).timestamp() - (i * 3600)
        start = datetime.fromtimestamp(bucket, tz=timezone.utc)
        end = datetime.fromtimestamp(bucket + 3600, tz=timezone.utc)
        events = await db.scalar(select(func.count(Event.id)).where(Event.timestamp >= start, Event.timestamp < end))
        alerts = await db.scalar(select(func.count(Alert.alert_id)).where(Alert.timestamp >= start, Alert.timestamp < end))
        rows.append(TimelinePoint(bucket=start.isoformat(), events=events or 0, alerts=alerts or 0))
    return rows
