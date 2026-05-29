from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.alert import Alert
from backend.models.event import Event
from backend.schemas.stats import StatsSummary, TimelinePoint


async def get_alert_counts_by_severity(db: AsyncSession) -> dict[str, int]:
    rows = await db.execute(select(Alert.severity, func.count(Alert.alert_id)).group_by(Alert.severity))
    return {severity: count for severity, count in rows.all()}


async def get_stats_summary(db: AsyncSession) -> StatsSummary:
    event_count = await db.scalar(select(func.count(Event.event_id)))
    alert_count = await db.scalar(select(func.count(Alert.alert_id)))
    by_severity = await get_alert_counts_by_severity(db)
    return StatsSummary(
        total_events=event_count or 0,
        total_alerts=alert_count or 0,
        alerts_by_severity=by_severity,
    )


async def get_timeline(db: AsyncSession) -> list[TimelinePoint]:
    now = datetime.now(timezone.utc)
    rows: list[TimelinePoint] = []
    current_bucket = now.replace(minute=0, second=0, microsecond=0)

    for index in range(6, -1, -1):
        bucket_start = current_bucket - timedelta(hours=index)
        bucket_end = bucket_start + timedelta(hours=1)
        events = await db.scalar(
            select(func.count(Event.event_id)).where(Event.timestamp >= bucket_start, Event.timestamp < bucket_end)
        )
        alerts = await db.scalar(
            select(func.count(Alert.alert_id)).where(Alert.created_at >= bucket_start, Alert.created_at < bucket_end)
        )
        rows.append(TimelinePoint(bucket=bucket_start.isoformat(), events=events or 0, alerts=alerts or 0))
    return rows
