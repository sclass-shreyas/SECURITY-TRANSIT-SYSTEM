"""Unattended baggage detection module."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import config


class UnattendedObjectDetector:
    """Detect unattended objects by measuring person proximity over time."""

    def __init__(self) -> None:
        """Initialize unattended tracking state."""
        self._first_unattended_at: dict[int, float] = {}
        self._alerted_bag_ids: set[int] = set()

    @staticmethod
    def euclidean_distance(p1: list[int], p2: list[int]) -> float:
        """Compute Euclidean distance between two points.

        Args:
            p1: First point [x, y].
            p2: Second point [x, y].

        Returns:
            Euclidean distance.
        """
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def analyze(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze event objects for unattended baggage.

        Args:
            event: Detection event payload.

        Returns:
            Raw unattended_object alerts.
        """
        frame_id = int(event.get("frame_id", -1))
        timestamp_iso = str(event.get("timestamp"))
        current_time = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00")).timestamp()

        persons = [obj for obj in event.get("objects", []) if obj.get("class_name") == "person"]
        bags = [
            obj
            for obj in event.get("objects", [])
            if obj.get("class_name") in {"backpack", "handbag", "suitcase"}
        ]

        alerts: list[dict[str, Any]] = []

        for bag in bags:
            bag_id = int(bag.get("object_id", -1))
            bag_centroid = bag.get("centroid", [0, 0])

            near_person = any(
                self.euclidean_distance(bag_centroid, person.get("centroid", [0, 0])) <= 150.0
                for person in persons
            )

            if near_person:
                self._first_unattended_at.pop(bag_id, None)
                self._alerted_bag_ids.discard(bag_id)
                continue

            if bag_id not in self._first_unattended_at:
                self._first_unattended_at[bag_id] = current_time
                continue

            unattended_seconds = current_time - self._first_unattended_at[bag_id]
            if unattended_seconds <= config.UNATTENDED_THRESHOLD_SECONDS:
                continue

            if bag_id in self._alerted_bag_ids:
                continue

            self._alerted_bag_ids.add(bag_id)
            zones = bag.get("zones", [""])
            alerts.append(
                {
                    "alert_type": "unattended_object",
                    "object_id": bag_id,
                    "class_name": str(bag.get("class_name", "unknown")),
                    "zone": str(zones[0] if zones else ""),
                    "metadata": {
                        "dwell_seconds": float(unattended_seconds),
                        "person_count": len(persons),
                        "confidence": float(bag.get("confidence", 0.0)),
                        "frame_id": frame_id,
                    },
                }
            )

        return alerts
