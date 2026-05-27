"""Loitering detection module for transit security analytics."""

from __future__ import annotations

from typing import Any

import config


class LoiteringDetector:
    """Detect loitering behavior from tracked object dwell times."""

    def __init__(self) -> None:
        """Initialize detector state."""
        self._triggered_object_ids: set[int] = set()

    def analyze(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze event objects and produce raw loitering alerts.

        Args:
            event: Detection event payload.

        Returns:
            Raw alert dictionaries for objects exceeding loitering threshold.
        """
        raw_alerts: list[dict[str, Any]] = []
        for obj in event.get("objects", []):
            object_id = int(obj.get("object_id", -1))
            dwell_seconds = float(obj.get("dwell_seconds", 0.0))

            if dwell_seconds <= config.LOITERING_THRESHOLD_SECONDS:
                continue

            if object_id in self._triggered_object_ids:
                continue

            self._triggered_object_ids.add(object_id)
            zone = obj.get("zones", [""])
            raw_alerts.append(
                {
                    "alert_type": "loitering",
                    "object_id": object_id,
                    "class_name": str(obj.get("class_name", "unknown")),
                    "zone": str(zone[0] if zone else ""),
                    "metadata": {
                        "dwell_seconds": dwell_seconds,
                        "person_count": 0,
                        "confidence": float(obj.get("confidence", 0.0)),
                        "frame_id": int(event.get("frame_id", -1)),
                    },
                }
            )

        return raw_alerts

    def reset(self, object_id: int) -> None:
        """Clear loitering-triggered state for an object.

        Args:
            object_id: Tracked object identifier.
        """
        self._triggered_object_ids.discard(object_id)
