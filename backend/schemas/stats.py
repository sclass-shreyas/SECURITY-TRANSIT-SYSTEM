from __future__ import annotations

from pydantic import BaseModel


class AlertStats(BaseModel):
    """Aggregate alert and event counts for the dashboard."""

    total_alerts: int
    by_type: dict[str, int]
    by_severity: dict[str, int]
    most_active_zone: str | None
    high_severity_count: int
    total_events: int
