"""Entry point for real-time smart transit security detection pipeline."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2

import config
from capture import FrameCapture
from detector import Detector
from event_publisher import EventPublisher
from tracker import ObjectTracker
from zone_manager import ZoneManager


def _setup_logging() -> None:
    """Configure process-wide logging."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _centroid_from_bbox(bbox: list[int]) -> list[int]:
    """Compute centroid from an xyxy bounding box."""
    x1, y1, x2, y2 = bbox
    return [(x1 + x2) // 2, (y1 + y2) // 2]


def _build_event(
    frame_id: int,
    tracked_objects: list[dict[str, Any]],
    zone_manager: ZoneManager,
    timestamp_epoch: float,
) -> dict[str, Any]:
    """Construct event payload matching required schema."""
    payload_objects: list[dict[str, Any]] = []

    for obj in tracked_objects:
        zones = zone_manager.get_zones_for_object(obj["bbox"])
        dwell_by_zone = zone_manager.update_dwell(obj["object_id"], zones, timestamp_epoch)
        max_dwell = max(dwell_by_zone.values(), default=0.0)
        restricted_alert = any(zone_manager.zones[zone_id]["restricted"] for zone_id in zones)

        payload_objects.append(
            {
                "object_id": obj["object_id"],
                "class_name": obj["class_name"],
                "confidence": round(float(obj["confidence"]), 2),
                "bbox": obj["bbox"],
                "centroid": _centroid_from_bbox(obj["bbox"]),
                "zones": zones,
                "dwell_seconds": round(float(max_dwell), 2),
                "restricted_zone_alert": restricted_alert,
            }
        )

    return {
        "event_id": str(uuid4()),
        "frame_id": frame_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "objects": payload_objects,
    }


def _draw_overlays(frame: Any, tracked_objects: list[dict[str, Any]], zone_manager: ZoneManager) -> None:
    """Draw zones and tracked object overlays on frame."""
    for zone in zone_manager.zones.values():
        color = (0, 0, 255) if zone["restricted"] else (0, 255, 0)
        cv2.polylines(frame, [zone["polygon"]], True, color, 2)
        label_anchor = tuple(zone["polygon"][0])
        cv2.putText(
            frame,
            f"{zone['id']}:{zone['name']}",
            label_anchor,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )

    for obj in tracked_objects:
        x1, y1, x2, y2 = obj["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(
            frame,
            f"ID {obj['object_id']} {obj['class_name']}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            2,
            cv2.LINE_AA,
        )


async def main() -> None:
    """Run the async real-time detection, tracking, zoning, and publishing loop."""
    _setup_logging()
    logger = logging.getLogger("main")

    base_dir = Path(__file__).resolve().parent
    zones_path = str(base_dir / config.ZONES_FILE)

    capture = FrameCapture(config.CAMERA_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT)
    detector = Detector()
    tracker = ObjectTracker()
    zone_manager = ZoneManager(zones_path)
    publisher = EventPublisher()

    frame_id = 0
    fps_window_start = time.perf_counter()

    try:
        while True:
            loop_start = time.perf_counter()

            success, frame = capture.read_frame()
            if not success:
                logger.warning("Failed to read frame; continuing.")
                await asyncio.sleep(0)
                continue

            detections = detector.detect(frame)
            tracked_objects = tracker.update(detections, frame)

            now = time.time()
            event = _build_event(frame_id, tracked_objects, zone_manager, now)
            await publisher.publish(event)

            _draw_overlays(frame, tracked_objects, zone_manager)
            cv2.imshow(config.WINDOW_NAME, frame)

            frame_id += 1
            if frame_id % config.FPS_LOG_INTERVAL == 0:
                elapsed = time.perf_counter() - fps_window_start
                fps = config.FPS_LOG_INTERVAL / elapsed if elapsed > 0 else 0.0
                logger.info("Processed %s frames. Actual FPS: %.2f", frame_id, fps)
                fps_window_start = time.perf_counter()

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            elapsed_loop = time.perf_counter() - loop_start
            sleep_time = max(0.0, config.TARGET_FRAME_TIME_SECONDS - elapsed_loop)
            await asyncio.sleep(sleep_time)

    finally:
        capture.release()
        await publisher.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
