from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalyticsResultIn(BaseModel):
    result_id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    detector_type: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsResultOut(BaseModel):
    result_id: UUID
    event_id: UUID
    detector_type: str
    confidence: float
    metadata: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def deserialize_metadata(cls, data: Any) -> Any:
        """Convert ORM metadata_json into the public metadata field."""
        if isinstance(data, dict):
            metadata_json = data.get("metadata_json")
            if "metadata" not in data and metadata_json is not None:
                data["metadata"] = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            if "created_at" not in data or data.get("created_at") is None:
                data["created_at"] = datetime.now(timezone.utc)
            return data

        if hasattr(data, "metadata_json"):
            metadata_json = data.metadata_json
            return {
                "result_id": data.result_id,
                "event_id": data.event_id,
                "detector_type": data.detector_type,
                "confidence": data.confidence,
                "metadata": json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json,
                "created_at": getattr(data, "created_at", None) or datetime.now(timezone.utc),
            }
        return data
