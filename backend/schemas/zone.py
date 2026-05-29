from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ZoneIn(BaseModel):
    """Inbound zone creation payload."""

    zone_id: str
    name: str
    restricted: bool = False
    polygon: list[list[int]]


class ZoneOut(BaseModel):
    """Outbound zone payload."""

    id: int
    zone_id: str
    name: str
    restricted: bool
    polygon: list[list[int]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def deserialize_polygon(cls, data: Any) -> Any:
        """Convert ORM polygon_json into the public polygon field."""
        if isinstance(data, dict):
            polygon_json = data.get("polygon_json")
            if "polygon" not in data and polygon_json is not None:
                data["polygon"] = json.loads(polygon_json)
            return data

        if hasattr(data, "polygon_json"):
            return {
                "id": data.id,
                "zone_id": data.zone_id,
                "name": data.name,
                "restricted": data.restricted,
                "polygon": json.loads(data.polygon_json),
                "created_at": data.created_at,
            }
        return data
