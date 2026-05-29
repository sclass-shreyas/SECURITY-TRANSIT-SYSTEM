from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


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
