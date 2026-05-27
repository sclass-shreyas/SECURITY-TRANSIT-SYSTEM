from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertIn(BaseModel):
    alert_id: str
    alert_type: str
    severity: str
    timestamp: datetime
    object_id: int
    class_name: str
    zone: str
    clip_path: str = ""
    metadata: dict = Field(default_factory=dict)


class AlertOut(BaseModel):
    alert_id: str
    alert_type: str
    severity: str
    timestamp: datetime
    object_id: int
    class_name: str
    zone: str
    clip_path: str
    metadata: dict

    model_config = ConfigDict(from_attributes=True)
