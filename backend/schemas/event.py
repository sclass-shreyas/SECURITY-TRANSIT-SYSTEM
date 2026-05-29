from __future__ import annotations

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

    frame_id: int
    timestamp: str
    objects: list[DetectedObject]
