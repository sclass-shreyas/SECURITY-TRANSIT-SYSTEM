from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DetectionObjectIn(BaseModel):
    object_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int] = Field(min_length=4, max_length=4)
    centroid: list[int] = Field(min_length=2, max_length=2)
    zones: list[str] = Field(default_factory=list)
    dwell_seconds: float = Field(default=0.0, ge=0.0)
    restricted_zone_alert: bool = False

    model_config = ConfigDict(extra="allow")


class EventIn(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    schema_version: str = "1.0"
    camera_id: UUID | None = None
    frame_id: int = Field(ge=0)
    timestamp: datetime
    objects: list[DetectionObjectIn] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")
