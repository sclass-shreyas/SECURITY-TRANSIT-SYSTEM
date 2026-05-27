from pydantic import BaseModel


class StatsSummary(BaseModel):
    total_events: int
    total_alerts: int
    alerts_by_severity: dict[str, int]


class TimelinePoint(BaseModel):
    bucket: str
    events: int
    alerts: int
