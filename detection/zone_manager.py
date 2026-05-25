"""Zone management and dwell-time logic for tracked objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class ZoneManager:
    """Load polygon zones, test object membership, and track dwell times."""

    def __init__(self, zones_file: str) -> None:
        """Initialize manager and load zones from JSON file."""
        self.zones_path = Path(zones_file)
        self.zones: dict[str, dict[str, Any]] = {}
        self._dwell_started_at: dict[tuple[int, str], float] = {}
        self.reload_zones()

    def reload_zones(self) -> None:
        """Reload zone definitions from disk without restarting."""
        with self.zones_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        loaded: dict[str, dict[str, Any]] = {}
        for zone in data.get("zones", []):
            zone_id = zone["id"]
            loaded[zone_id] = {
                "id": zone_id,
                "name": zone["name"],
                "restricted": bool(zone["restricted"]),
                "polygon": np.array(zone["polygon"], dtype=np.int32),
            }
        self.zones = loaded

    def is_in_zone(self, point: tuple[int, int], zone_id: str) -> bool:
        """Return True when a point lies inside or on the edge of a zone polygon."""
        zone = self.zones.get(zone_id)
        if zone is None:
            return False

        x, y = point
        result = cv2.pointPolygonTest(zone["polygon"], (float(x), float(y)), False)
        return result >= 0

    def get_zones_for_object(self, bbox: list[int]) -> list[str]:
        """Return zone IDs containing the object centroid."""
        x1, y1, x2, y2 = bbox
        centroid = ((x1 + x2) // 2, (y1 + y2) // 2)

        return [zone_id for zone_id in self.zones if self.is_in_zone(centroid, zone_id)]

    def update_dwell(self, object_id: int, zone_ids: list[str], timestamp: float) -> dict[str, float]:
        """Update and return dwell times for the object's currently occupied zones.

        Clears any stored dwell records for zones the object has left.
        """
        current = set(zone_ids)
        keys = [key for key in self._dwell_started_at if key[0] == object_id]

        for key in keys:
            _, zone_id = key
            if zone_id not in current:
                del self._dwell_started_at[key]

        dwell_times: dict[str, float] = {}
        for zone_id in zone_ids:
            key = (object_id, zone_id)
            if key not in self._dwell_started_at:
                self._dwell_started_at[key] = timestamp
            dwell_times[zone_id] = max(0.0, timestamp - self._dwell_started_at[key])

        return dwell_times
