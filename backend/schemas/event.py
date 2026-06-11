from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DetectedObject(BaseModel):
    """Detected object emitted by the P1 detection pipeline."""

    object_id: int
    class_name: str
    confidence: float
    bbox: list[int]
    centroid: list[int]
    zones: list[str]
    dwell_seconds: float
    restricted_zone_alert: bool


class EventIn(BaseModel):
    """Inbound detection event payload."""

    event_id: UUID | None = None
    correlation_id: UUID | None = None
    schema_version: str = "1.0"
    camera_id: UUID | None = None
    frame_id: int
    timestamp: datetime
    objects: list[DetectedObject]
