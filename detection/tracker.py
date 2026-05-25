"""DeepSORT tracking wrapper for stable object identity across frames."""

from __future__ import annotations

from typing import Any

import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort


class ObjectTracker:
    """Track detections and return confirmed tracked objects."""

    def __init__(self) -> None:
        """Initialize DeepSORT tracker with balanced defaults."""
        self.tracker = DeepSort(max_age=30, n_init=2)

    def update(self, detections: list[dict[str, Any]], frame: np.ndarray) -> list[dict[str, Any]]:
        """Update tracker state and return confirmed tracks.

        Args:
            detections: Detector output list.
            frame: Current frame.

        Returns:
            List of tracked object dictionaries.
        """
        if not detections:
            return []

        ds_inputs = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            ds_inputs.append(
                ([x1, y1, x2 - x1, y2 - y1], det["confidence"], det["class_name"])
            )

        tracks = self.tracker.update_tracks(ds_inputs, frame=frame)

        tracked_objects: list[dict[str, Any]] = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            ltrb = track.to_ltrb()
            if ltrb is None:
                continue

            x1, y1, x2, y2 = ltrb
            class_name = track.get_det_class() or "unknown"
            confidence = float(track.get_det_conf() or 0.0)
            tracked_objects.append(
                {
                    "object_id": int(track.track_id),
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                }
            )

        return tracked_objects
