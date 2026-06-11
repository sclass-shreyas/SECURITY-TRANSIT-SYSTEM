from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ZoneIn(BaseModel):
    """Inbound zone creation payload."""

    zone_id: str | None = None
    name: str | None = None
    zone_name: str | None = None
    restricted: bool = False
    polygon: list[list[int]] | None = None
    polygon_points_json: list[list[int]] | None = None

    @model_validator(mode="after")
    def normalize_fields(self) -> "ZoneIn":
        """Populate the legacy and PostgreSQL field names from either input shape."""
        if self.zone_name and not self.name:
            self.name = self.zone_name
        if self.name and not self.zone_name:
            self.zone_name = self.name
        if self.zone_id is None and self.zone_name:
            self.zone_id = self.zone_name
        if self.name is None and self.zone_id is not None:
            self.name = self.zone_id
        if self.polygon is None and self.polygon_points_json is not None:
            self.polygon = self.polygon_points_json
        if self.polygon_points_json is None and self.polygon is not None:
            self.polygon_points_json = self.polygon
        return self


class ZoneOut(BaseModel):
    """Outbound zone payload."""

    id: int
    zone_id: str | None = None
    name: str | None = None
    zone_name: str | None = None
    restricted: bool
    polygon: list[list[int]] | None = None
    polygon_points_json: list[list[int]] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def deserialize_polygon(cls, data: Any) -> Any:
        """Convert ORM polygon_json into the public polygon field."""
        if isinstance(data, dict):
            polygon_json = data.get("polygon_json")
            polygon_points_json = data.get("polygon_points_json")
            if "polygon" not in data:
                if polygon_json is not None:
                    data["polygon"] = json.loads(polygon_json)
                elif polygon_points_json is not None:
                    data["polygon"] = polygon_points_json
            if "polygon_points_json" not in data and data.get("polygon") is not None:
                data["polygon_points_json"] = data["polygon"]
            if "zone_name" not in data and data.get("name") is not None:
                data["zone_name"] = data["name"]
            if "name" not in data and data.get("zone_name") is not None:
                data["name"] = data["zone_name"]
            return data

        if hasattr(data, "polygon_json") or hasattr(data, "polygon_points_json"):
            polygon = (
                json.loads(data.polygon_json)
                if hasattr(data, "polygon_json")
                else getattr(data, "polygon_points_json")
            )
            return {
                "id": data.id,
                "zone_id": getattr(data, "zone_id", None),
                "name": getattr(data, "name", None),
                "zone_name": getattr(data, "zone_name", None) or getattr(data, "name", None),
                "restricted": data.restricted,
                "polygon": polygon,
                "polygon_points_json": polygon,
                "created_at": data.created_at,
            }
        return data
