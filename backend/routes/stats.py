from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Request
from sqlalchemy import select

from backend.models.alert import Alert
from backend.models.event import Event
from backend.schemas.stats import AlertStats

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/", response_model=AlertStats)
async def read_stats(request: Request) -> AlertStats:
    """Return dashboard aggregate statistics."""
    async with request.app.state.sessionmaker() as session:
        alert_rows = (await session.execute(select(Alert))).scalars().all()
        event_rows = (await session.execute(select(Event))).scalars().all()

    by_type = Counter(str(alert.alert_type) for alert in alert_rows)
    by_severity = Counter(str(alert.severity) for alert in alert_rows)
    zone_counter = Counter(str(alert.zone) for alert in alert_rows if str(alert.zone))
    most_active_zone = zone_counter.most_common(1)[0][0] if zone_counter else None

    return AlertStats(
        total_alerts=len(alert_rows),
        by_type=dict(by_type),
        by_severity=dict(by_severity),
        most_active_zone=most_active_zone,
        high_severity_count=sum(1 for alert in alert_rows if str(alert.severity).lower() == "high"),
        total_events=len(event_rows),
    )
