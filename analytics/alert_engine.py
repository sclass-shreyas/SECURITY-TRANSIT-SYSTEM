"""Alert post-processing engine for severity scoring, dedup, and clip creation."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

import config


class AlertEngine:
    """Finalize raw alerts with deduplication, severity, and clip attachment."""

    def __init__(self) -> None:
        """Initialize deduplication state and frame buffer."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._last_alert_times: dict[tuple[str, int], float] = {}
        self._frame_buffer: deque[np.ndarray] = deque(
            maxlen=config.CLIP_DURATION_SECONDS * config.TARGET_FPS
        )
        self._clips_dir = Path(__file__).resolve().parent / config.CLIPS_DIR
        self._clips_dir.mkdir(parents=True, exist_ok=True)

    def update_frame_buffer(self, frame: np.ndarray) -> None:
        """Append frame to rolling clip buffer.

        Args:
            frame: Current BGR frame.
        """
        if frame is None or frame.size == 0:
            return
        self._frame_buffer.append(frame.copy())

    def _is_duplicate(self, alert_type: str, object_id: int) -> bool:
        """Check whether alert duplicates recent alert within dedup window."""
        now = time.time()
        key = (alert_type, object_id)
        last_time = self._last_alert_times.get(key)
        if last_time is not None and (now - last_time) < config.DEDUP_WINDOW_SECONDS:
            return True
        self._last_alert_times[key] = now
        return False

    def _score_severity(self, raw_alert: dict[str, Any]) -> str:
        """Assign severity according to fixed scoring rules."""
        alert_type = raw_alert["alert_type"]
        metadata = raw_alert.get("metadata", {})

        if alert_type == "loitering":
            dwell_seconds = float(metadata.get("dwell_seconds", 0.0))
            if dwell_seconds < 20:
                return "low"
            if dwell_seconds <= 40:
                return "medium"
            return "high"

        if alert_type == "crowd_surge":
            person_count = int(metadata.get("person_count", 0))
            if 5 <= person_count <= 7:
                return "low"
            if 8 <= person_count <= 10:
                return "medium"
            if person_count > 10:
                return "high"
            return "low"

        if alert_type == "unattended_object":
            return "high"

        if alert_type == "theft_gesture":
            confidence = float(metadata.get("confidence", 0.0))
            if confidence < 0.6:
                return "low"
            if confidence <= 0.8:
                return "medium"
            return "high"

        if alert_type == "restricted_zone":
            return "high"

        return "low"

    def _save_clip(self, alert_id: str, frames: deque[np.ndarray]) -> str:
        """Persist clip from buffered frames and return relative clip path."""
        if not frames:
            self.logger.warning("No frames available for clip: %s", alert_id)
            return ""

        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            file_name = f"alert_{alert_id[:8]}_{timestamp}.avi"
            output_path = self._clips_dir / file_name

            first_frame = frames[0]
            height, width = first_frame.shape[:2]
            
            if height <= 0 or width <= 0:
                self.logger.error("Invalid frame dimensions: %dx%d", width, height)
                return ""
            
            writer = cv2.VideoWriter(
                str(output_path),
                cv2.VideoWriter_fourcc(*"XVID"),
                config.TARGET_FPS,
                (width, height),
            )

            if not writer.isOpened():
                self.logger.error("Failed to open VideoWriter for %s", output_path)
                return ""

            try:
                for frame in frames:
                    if frame is not None and frame.size > 0:
                        writer.write(frame)
            finally:
                writer.release()

            self.logger.info("Saved clip: %s", file_name)
            return str(Path(config.CLIPS_DIR) / file_name)
        except Exception as e:
            self.logger.error("Error saving clip %s: %s", alert_id, e, exc_info=True)
            return ""

    async def process(
        self,
        raw_alerts: list[dict[str, Any]],
        event: dict[str, Any],
        frame: np.ndarray,
    ) -> list[dict[str, Any]]:
        """Finalize raw alerts into alert schema records.

        Args:
            raw_alerts: Raw alerts from detector modules.
            event: Source event payload.
            frame: Current frame.

        Returns:
            Finalized alerts matching the strict schema.
        """
        self.update_frame_buffer(frame)

        finalized: list[dict[str, Any]] = []
        for raw in raw_alerts:
            try:
                alert_type = str(raw.get("alert_type", ""))
                object_id = int(raw.get("object_id", -1))

                if self._is_duplicate(alert_type, object_id):
                    continue

                alert_id = str(uuid.uuid4())
                severity = self._score_severity(raw)

                clip_frames = deque(self._frame_buffer)
                try:
                    clip_path = await asyncio.to_thread(self._save_clip, alert_id, clip_frames)
                except Exception as e:
                    self.logger.error("Failed to save clip for alert %s: %s", alert_id, e)
                    clip_path = ""

                metadata = raw.get("metadata", {})
                finalized.append(
                    {
                        "alert_id": alert_id,
                        "alert_type": alert_type,
                        "severity": severity,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "object_id": object_id,
                        "class_name": str(raw.get("class_name", "unknown")),
                        "zone": str(raw.get("zone", "")),
                        "clip_path": clip_path,
                        "metadata": {
                            "dwell_seconds": float(metadata.get("dwell_seconds", 0.0)),
                            "person_count": int(metadata.get("person_count", 0)),
                            "confidence": float(metadata.get("confidence", 0.0)),
                            "frame_id": int(metadata.get("frame_id", event.get("frame_id", -1))),
                        },
                    }
                )
            except Exception as e:
                self.logger.error("Error processing alert: %s", e, exc_info=True)
                continue

        return finalized
