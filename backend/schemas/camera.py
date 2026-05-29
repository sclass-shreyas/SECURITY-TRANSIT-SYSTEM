from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CameraIn(BaseModel):
    camera_id: UUID | None = None
    camera_name: str = Field(min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class CameraOut(BaseModel):
    camera_id: UUID
    camera_name: str
    location: str | None
    is_active: bool
    metadata: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
