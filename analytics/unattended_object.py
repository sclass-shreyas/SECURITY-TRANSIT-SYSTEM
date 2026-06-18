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
        self._bag_owners: dict[int, int] = {}  # bag_id -> owner_person_id
        self._bag_last_position: dict[int, list[int]] = {}  # bag_id -> [x, y]
        self._bag_owner_last_seen: dict[int, float] = {}  # bag_id -> last_time_owner_nearby

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

        # Create person ID to object mapping for quick lookup
        person_ids = {int(p.get("object_id", -1)): p for p in persons}

        for bag in bags:
            bag_id = int(bag.get("object_id", -1))
            bag_centroid = bag.get("centroid", [0, 0])

            # Check if any person is near the bag
            near_person = None
            min_distance = float('inf')
            for person in persons:
                distance = self.euclidean_distance(bag_centroid, person.get("centroid", [0, 0]))
                if distance <= config.OBJECT_PROXIMITY_THRESHOLD and distance < min_distance:
                    near_person = person
                    min_distance = distance

            # If person nearby, assign as owner if not already assigned
            if near_person:
                owner_id = int(near_person.get("object_id", -1))
                if bag_id not in self._bag_owners:
                    # New bag detected, assign nearest person as owner
                    self._bag_owners[bag_id] = owner_id
                    self._bag_last_position[bag_id] = bag_centroid.copy()
                    self._bag_owner_last_seen[bag_id] = current_time
                else:
                    # Owner still nearby or new owner is closer
                    self._bag_owner_last_seen[bag_id] = current_time
                
                # Reset unattended timer when owner is nearby
                self._first_unattended_at.pop(bag_id, None)
                self._alerted_bag_ids.discard(bag_id)
                continue

            # No person nearby - bag is unattended
            # Only start timer if owner has been away for a moment (owner departure detected)
            owner_id = self._bag_owners.get(bag_id, -1)
            time_since_owner_seen = current_time - self._bag_owner_last_seen.get(bag_id, current_time)
            
            # Require owner to be away for grace period before starting unattended timer
            if time_since_owner_seen < config.OWNER_DEPARTURE_GRACE_SECONDS:
                # Owner just left, don't start timer yet
                continue

            # Check if bag has moved significantly (stationarity check)
            if bag_id in self._bag_last_position:
                last_pos = self._bag_last_position[bag_id]
                movement = self.euclidean_distance(bag_centroid, last_pos)
                if movement > config.OBJECT_STATIONARITY_THRESHOLD:  # Bag moved too much
                    # Bag is moving, reset timer
                    self._first_unattended_at.pop(bag_id, None)
                    self._alerted_bag_ids.discard(bag_id)
                    self._bag_last_position[bag_id] = bag_centroid.copy()
                    continue
            
            self._bag_last_position[bag_id] = bag_centroid.copy()

            # Start/continue unattended timer
            if bag_id not in self._first_unattended_at:
                self._first_unattended_at[bag_id] = current_time
                continue

            unattended_seconds = current_time - self._first_unattended_at[bag_id]
            if unattended_seconds <= config.UNATTENDED_THRESHOLD_SECONDS:
                continue

            if bag_id in self._alerted_bag_ids:
                continue

            # Generate alert with owner information
            self._alerted_bag_ids.add(bag_id)
            zones = bag.get("zones", [""])
            owner_name = "unknown"
            if owner_id != -1 and owner_id in person_ids:
                owner_name = f"person_{owner_id}"
            
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
                        "owner_id": owner_id,
                        "owner_name": owner_name,
                        "stationary": True,
                    },
                }
            )

        # Clean up disappeared bags
        disappeared_bags = [bid for bid in self._bag_owners if bid not in [int(b.get("object_id", -1)) for b in bags]]
        for bid in disappeared_bags:
            self._bag_owners.pop(bid, None)
            self._bag_last_position.pop(bid, None)
            self._bag_owner_last_seen.pop(bid, None)
            self._first_unattended_at.pop(bid, None)
            self._alerted_bag_ids.discard(bid)

        return alerts
