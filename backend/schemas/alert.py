from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class AlertMetadata(BaseModel):
    """Structured metadata attached to an analytics alert."""

    dwell_seconds: float = 0.0
    person_count: int = 0
    confidence: float = 0.0
    frame_id: int = -1


class AlertIn(BaseModel):
    """Inbound alert payload from the P2 analytics pipeline."""

    alert_id: UUID | None = None
    event_id: UUID | None = None
    alert_type: str
    severity: str
    timestamp: datetime
    object_id: int
    class_name: str
    zone: str
    status: str = "open"
    resolved_at: datetime | None = None
    clip_path: str | None = None
    metadata: AlertMetadata


class AlertOut(BaseModel):
    """Outbound alert payload returned by backend APIs."""

    id: int
    alert_id: str
    event_id: str | None = None
    alert_type: str
    severity: str
    status: str = "open"
    object_id: int
    class_name: str
    zone: str
    clip_path: str | None
    metadata: AlertMetadata
    timestamp: datetime
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def deserialize_metadata(cls, data: Any) -> Any:
        """Convert ORM metadata_json into the public metadata field."""
        if isinstance(data, dict):
            metadata_json = data.get("metadata_json")
            if "metadata" not in data and metadata_json is not None:
                data["metadata"] = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            if "alert_id" in data and data.get("alert_id") is not None:
                data["alert_id"] = str(data["alert_id"])
            if "event_id" in data and data.get("event_id") is not None:
                data["event_id"] = str(data["event_id"])
            if "id" not in data or data.get("id") is None:
                data["id"] = 0
            return data

        if hasattr(data, "metadata_json"):
            metadata_json = data.metadata_json
            return {
                "id": getattr(data, "id", 0) or 0,
                "alert_id": str(data.alert_id),
                "event_id": str(getattr(data, "event_id", None)) if getattr(data, "event_id", None) is not None else None,
                "alert_type": data.alert_type,
                "severity": data.severity,
                "status": getattr(data, "status", "open"),
                "object_id": data.object_id,
                "class_name": data.class_name,
                "zone": data.zone,
                "clip_path": data.clip_path,
                "metadata": json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json,
                "timestamp": data.timestamp,
                "created_at": data.created_at,
                "resolved_at": getattr(data, "resolved_at", None),
            }
        return data
