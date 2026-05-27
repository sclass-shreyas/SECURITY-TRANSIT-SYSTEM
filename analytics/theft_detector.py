"""Theft gesture detection module using MediaPipe Pose landmarks."""

from __future__ import annotations

import logging
import math
import time
from typing import Any

import cv2
import numpy as np

import config

try:
    import mediapipe as mp
except Exception:  # pragma: no cover
    mp = None  # type: ignore[assignment]


class TheftDetector:
    """Detect potential theft gestures from wrist velocity and hip proximity."""

    def __init__(self) -> None:
        """Initialize MediaPipe pose and temporal landmark state."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._previous_landmarks: dict[int, dict[str, Any]] = {}

        self._enabled = mp is not None
        self._mp_pose = None
        self.pose = None

        if not self._enabled:
            self.logger.warning("mediapipe is not installed. Theft detection disabled.")
            return

        self._mp_pose = mp.solutions.pose
        self.pose = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        if config.DEVICE == "cuda":
            self.logger.warning(
                "MediaPipe Pose uses CPU runtime. CUDA fallback is not available for this backend."
            )

    def update_landmarks(self, object_id: int, landmarks: dict[str, tuple[float, float]]) -> None:
        """Store previous landmarks for an object for velocity estimation.

        Args:
            object_id: Tracked object identifier.
            landmarks: Landmark coordinates by key.
        """
        self._previous_landmarks[object_id] = {
            "timestamp": time.time(),
            "landmarks": landmarks,
        }

    @staticmethod
    def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        """Compute Euclidean distance between two 2D points."""
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _compute_confidence(
        self,
        object_id: int,
        wrist: tuple[float, float],
        hip: tuple[float, float],
    ) -> float:
        """Compute gesture confidence from wrist velocity and hip proximity."""
        previous = self._previous_landmarks.get(object_id)
        now = time.time()

        velocity = 0.0
        if previous is not None:
            dt = max(1e-3, now - float(previous["timestamp"]))
            prev_wrist = previous["landmarks"].get("wrist")
            if prev_wrist is not None:
                velocity = self._distance(wrist, prev_wrist) / dt

        hip_dist = self._distance(wrist, hip)
        proximity_score = max(0.0, 1.0 - (hip_dist / max(config.THEFT_PROXIMITY_THRESHOLD, 1e-3)))
        velocity_score = min(1.0, velocity / max(config.THEFT_VELOCITY_THRESHOLD, 1e-3))

        return max(0.0, min(1.0, 0.6 * velocity_score + 0.4 * proximity_score))

    def analyze(self, frame: np.ndarray, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze frame and event data to detect theft-like gestures.

        Args:
            frame: Latest frame image.
            event: Detection event payload.

        Returns:
            Raw theft_gesture alerts.
        """
        if not self._enabled or self.pose is None or self._mp_pose is None:
            return []

        if frame is None or frame.size == 0:
            return []

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb_frame)
        if not result.pose_landmarks:
            return []

        lm = result.pose_landmarks.landmark
        left_wrist = lm[self._mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = lm[self._mp_pose.PoseLandmark.RIGHT_WRIST]
        left_hip = lm[self._mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = lm[self._mp_pose.PoseLandmark.RIGHT_HIP]

        wrist = (float((left_wrist.x + right_wrist.x) / 2.0), float((left_wrist.y + right_wrist.y) / 2.0))
        hip = (float((left_hip.x + right_hip.x) / 2.0), float((left_hip.y + right_hip.y) / 2.0))

        alerts: list[dict[str, Any]] = []
        frame_id = int(event.get("frame_id", -1))

        for obj in event.get("objects", []):
            if obj.get("class_name") != "person":
                continue

            object_id = int(obj.get("object_id", -1))
            confidence = self._compute_confidence(object_id, wrist, hip)
            self.update_landmarks(object_id, {"wrist": wrist, "hip": hip})

            if confidence <= config.THEFT_CONFIDENCE_THRESHOLD:
                continue

            zones = obj.get("zones", [""])
            alerts.append(
                {
                    "alert_type": "theft_gesture",
                    "object_id": object_id,
                    "class_name": "person",
                    "zone": str(zones[0] if zones else ""),
                    "metadata": {
                        "dwell_seconds": float(obj.get("dwell_seconds", 0.0)),
                        "person_count": len([o for o in event.get("objects", []) if o.get("class_name") == "person"]),
                        "confidence": float(confidence),
                        "frame_id": frame_id,
                    },
                }
            )

        return alerts
