from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AlertIn(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    event_id: UUID | None = None
    alert_type: str
    severity: str
    status: str = "open"
    timestamp: datetime
    resolved_at: datetime | None = None
    object_id: int
    class_name: str
    zone: str
    clip_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class AlertOut(BaseModel):
    alert_id: UUID
    event_id: UUID
    alert_type: str
    severity: str
    status: str
    timestamp: datetime
    resolved_at: datetime | None = None
    object_id: int
    class_name: str
    zone: str
    clip_path: str
    metadata: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
