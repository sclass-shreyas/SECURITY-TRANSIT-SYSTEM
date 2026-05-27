"""DeepSORT tracking wrapper for stable object identity across frames."""

from __future__ import annotations

from typing import Any

import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

import config


class ObjectTracker:
    """Track detections and return confirmed tracked objects."""

    def __init__(self) -> None:
        """Initialize DeepSORT tracker with balanced defaults."""
        self.tracker = DeepSort(max_age=config.TRACK_MAX_AGE, n_init=config.TRACK_N_INIT)
        self._confidence_cache: dict[int, float] = {}

    def update(self, detections: list[dict[str, Any]], frame: np.ndarray) -> list[dict[str, Any]]:
        """Update tracker state and return confirmed tracks."""
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

            raw_conf = track.get_det_conf()
            if raw_conf is None:
                self._confidence_cache.pop(int(track.track_id), None)
                continue

            x1, y1, x2, y2 = ltrb
            class_name = track.get_det_class() or "unknown"
            if raw_conf is not None:
                self._confidence_cache[track.track_id] = float(raw_conf)
            confidence = self._confidence_cache.get(track.track_id, 0.0)

            tracked_objects.append({
                "object_id": int(track.track_id),
                "class_name": class_name,
                "confidence": confidence,
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
            })

        return tracked_objects
