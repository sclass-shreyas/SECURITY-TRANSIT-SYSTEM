from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class AlertMetadata(BaseModel):
    """Structured metadata attached to an analytics alert."""

    dwell_seconds: float = 0.0
    person_count: int = 0
    confidence: float = 0.0
    frame_id: int = -1


class AlertIn(BaseModel):
    """Inbound alert payload from the P2 analytics pipeline."""

    alert_id: str
    alert_type: str
    severity: str
    timestamp: str
    object_id: int
    class_name: str
    zone: str
    clip_path: str | None = None
    metadata: AlertMetadata


class AlertOut(BaseModel):
    """Outbound alert payload returned by backend APIs."""

    id: int
    alert_id: str
    alert_type: str
    severity: str
    object_id: int
    class_name: str
    zone: str
    clip_path: str | None
    metadata: AlertMetadata
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def deserialize_metadata(cls, data: Any) -> Any:
        """Convert ORM metadata_json into the public metadata field."""
        if isinstance(data, dict):
            metadata_json = data.get("metadata_json")
            if "metadata" not in data and metadata_json is not None:
                data["metadata"] = json.loads(metadata_json)
            return data

        if hasattr(data, "metadata_json"):
            return {
                "id": data.id,
                "alert_id": data.alert_id,
                "alert_type": data.alert_type,
                "severity": data.severity,
                "object_id": data.object_id,
                "class_name": data.class_name,
                "zone": data.zone,
                "clip_path": data.clip_path,
                "metadata": json.loads(data.metadata_json),
                "timestamp": data.timestamp,
                "created_at": data.created_at,
            }
        return data
