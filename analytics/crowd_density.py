"""Crowd density and surge detection module."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import config


class CrowdDensityDetector:
    """Detect crowd surges globally and per zone from person counts."""

    def __init__(self) -> None:
        """Initialize detector state."""
        self._last_counts_by_zone: dict[str, int] = {}

    def analyze(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze crowd density and generate raw alerts.

        Args:
            event: Detection event payload.

        Returns:
            Raw crowd_surge alert dictionaries.
        """
        persons = [obj for obj in event.get("objects", []) if obj.get("class_name") == "person"]
        person_count = len(persons)

        zone_counts: defaultdict[str, int] = defaultdict(int)
        zone_counter: Counter[str] = Counter()

        for person in persons:
            zones = person.get("zones", [])
            if not zones:
                zone_counts[""] += 1
                continue
            for zone in zones:
                zone_id = str(zone)
                zone_counts[zone_id] += 1
                zone_counter[zone_id] += 1

        self._last_counts_by_zone = dict(zone_counts)
        frame_id = int(event.get("frame_id", -1))

        alerts: list[dict[str, Any]] = []

        # Check global threshold
        if person_count > config.CROWD_SURGE_THRESHOLD:
            dominant_zone = zone_counter.most_common(1)[0][0] if zone_counter else ""
            alerts.append(
                {
                    "alert_type": "crowd_surge",
                    "object_id": -1,
                    "class_name": "person",
                    "zone": dominant_zone,
                    "metadata": {
                        "dwell_seconds": 0.0,
                        "person_count": person_count,
                        "confidence": 0.0,
                        "frame_id": frame_id,
                        "surge_type": "global",
                    },
                }
            )

        # Check zone-specific thresholds
        for zone_id, count in zone_counts.items():
            # Get zone-specific threshold or use default
            zone_threshold = config.ZONE_CROWD_THRESHOLDS.get(zone_id, config.CROWD_SURGE_THRESHOLD)
            
            if count <= zone_threshold:
                continue
            
            # Avoid duplicate alert if already triggered by global threshold
            if zone_id and count == person_count:
                continue
                
            alerts.append(
                {
                    "alert_type": "crowd_surge",
                    "object_id": -1,
                    "class_name": "person",
                    "zone": zone_id,
                    "metadata": {
                        "dwell_seconds": 0.0,
                        "person_count": count,
                        "confidence": 0.0,
                        "frame_id": frame_id,
                        "surge_type": "zone_specific",
                    },
                }
            )

        return alerts
