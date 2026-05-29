from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import func, select

from backend.models import Alert, Event
from backend.schemas.stats import AlertStats

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/", response_model=AlertStats)
async def read_stats(request: Request) -> AlertStats:
    """Return dashboard aggregate statistics."""
    async with request.app.state.sessionmaker() as session:
        total_alerts = await session.scalar(select(func.count()).select_from(Alert))
        high_severity_count = await session.scalar(
            select(func.count()).select_from(Alert).where(Alert.severity == "high")
        )
        total_events = await session.scalar(select(func.count()).select_from(Event))

        type_rows = (
            await session.execute(select(Alert.alert_type, func.count()).group_by(Alert.alert_type))
        ).all()
        severity_rows = (
            await session.execute(select(Alert.severity, func.count()).group_by(Alert.severity))
        ).all()
        zone_row = (
            await session.execute(
                select(Alert.zone, func.count())
                .where(Alert.zone != "")
                .group_by(Alert.zone)
                .order_by(func.count().desc())
                .limit(1)
            )
        ).first()

    return AlertStats(
        total_alerts=int(total_alerts or 0),
        by_type={str(alert_type): int(count) for alert_type, count in type_rows},
        by_severity={str(severity): int(count) for severity, count in severity_rows},
        most_active_zone=str(zone_row[0]) if zone_row else None,
        high_severity_count=int(high_severity_count or 0),
        total_events=int(total_events or 0),
    )
