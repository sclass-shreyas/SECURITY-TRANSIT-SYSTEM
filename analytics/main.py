"""FastAPI entry point for analytics, alerts, and real-time alert streaming."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import config
from event_publisher import EventPublisher
from analytics_result_publisher import AnalyticsResultPublisher
from alert_engine import AlertEngine
from alert_publisher import AlertPublisher
from crowd_density import CrowdDensityDetector
from firebase_notifier import FirebaseNotifier
from loitering_detector import LoiteringDetector
from theft_detector import TheftDetector
from unattended_object import UnattendedObjectDetector

app = FastAPI(title="Smart Transit Analytics")
logger = logging.getLogger("analytics.main")

# Enable CORS for frontend dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manage active analytics WebSocket client connections."""

    def __init__(self) -> None:
        """Initialize WebSocket connection set."""
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection."""
        self._connections.discard(websocket)

    async def broadcast(self, alert: dict[str, Any]) -> None:
        """Broadcast one alert to all active clients."""
        stale: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_json(alert)
            except Exception:
                stale.append(connection)

        for connection in stale:
            self.disconnect(connection)


ws_manager = ConnectionManager()

# Track restricted zone violations to avoid spam
_restricted_zone_violations: set[tuple[int, str]] = set()  # (person_id, zone_id)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize analytics components and runtime state."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    clips_dir = Path(__file__).resolve().parent / config.CLIPS_DIR
    clips_dir.mkdir(parents=True, exist_ok=True)

    app.state.loitering_detector = LoiteringDetector()
    app.state.crowd_density = CrowdDensityDetector()
    app.state.unattended_object = UnattendedObjectDetector()
    app.state.theft_detector = TheftDetector()
    app.state.alert_engine = AlertEngine()
    app.state.event_publisher = EventPublisher()
    app.state.analytics_result_publisher = AnalyticsResultPublisher()
    app.state.firebase_notifier = FirebaseNotifier()
    app.state.alert_publisher = AlertPublisher()
    app.state.latest_frame = np.empty((0, 0, 3), dtype=np.uint8)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Release outbound publisher resources."""
    event_publisher: EventPublisher = app.state.event_publisher
    result_publisher: AnalyticsResultPublisher = app.state.analytics_result_publisher
    publisher: AlertPublisher = app.state.alert_publisher
    await event_publisher.close()
    await result_publisher.close()
    await publisher.close()


@app.post("/frame")
async def upload_frame(file: UploadFile = File(...)) -> dict[str, str]:
    """Receive latest frame bytes for analytics modules that require imagery.

    Note:
        P1 currently posts JSON-only events; P1 should also post JPEG frames
        to this endpoint for theft gesture analytics to be effective.
    """
    content = await file.read()
    frame_array = np.frombuffer(content, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    if frame is None or frame.size == 0:
        return {"status": "invalid_frame"}

    app.state.latest_frame = frame
    return {"status": "ok"}


@app.post("/events")
async def receive_event(event: dict[str, Any]) -> dict[str, int | str]:
    """Process incoming detection events and generate analytics alerts."""
    try:
        loitering_detector: LoiteringDetector = app.state.loitering_detector
        crowd_density: CrowdDensityDetector = app.state.crowd_density
        unattended_object: UnattendedObjectDetector = app.state.unattended_object
        theft_detector: TheftDetector = app.state.theft_detector
        alert_engine: AlertEngine = app.state.alert_engine
        analytics_result_publisher: AnalyticsResultPublisher = app.state.analytics_result_publisher
        firebase_notifier: FirebaseNotifier = app.state.firebase_notifier
        alert_publisher: AlertPublisher = app.state.alert_publisher

        frame = app.state.latest_frame
        raw_alerts: list[dict[str, Any]] = []

        try:
            raw_alerts.extend(loitering_detector.analyze(event))
        except Exception as e:
            logger.error("Error in loitering_detector: %s", e, exc_info=True)

        try:
            raw_alerts.extend(crowd_density.analyze(event))
        except Exception as e:
            logger.error("Error in crowd_density: %s", e, exc_info=True)

        try:
            raw_alerts.extend(unattended_object.analyze(event))
        except Exception as e:
            logger.error("Error in unattended_object: %s", e, exc_info=True)

        try:
            raw_alerts.extend(theft_detector.analyze(frame, event))
        except Exception as e:
            logger.error("Error in theft_detector: %s", e, exc_info=True)

        # Process restricted zone alerts (once per person per zone)
        try:
            for obj in event.get("objects", []):
                if obj.get("restricted_zone_alert"):
                    zones = obj.get("zones", [""])
                    object_id = int(obj.get("object_id", -1))
                    zone_id = str(zones[0] if zones else "")
                    
                    # Check if this person has already triggered an alert in this zone
                    violation_key = (object_id, zone_id)
                    if violation_key in _restricted_zone_violations:
                        # Already alerted for this person in this zone
                        continue
                    
                    # Mark this violation as alerted
                    _restricted_zone_violations.add(violation_key)
                    
                    raw_alerts.append(
                        {
                            "alert_type": "restricted_zone",
                            "object_id": object_id,
                            "class_name": str(obj.get("class_name", "unknown")),
                            "zone": zone_id,
                            "metadata": {
                                "dwell_seconds": float(obj.get("dwell_seconds", 0.0)),
                                "person_count": len(
                                    [p for p in event.get("objects", []) if p.get("class_name") == "person"]
                                ),
                                "confidence": float(obj.get("confidence", 0.0)),
                                "frame_id": int(event.get("frame_id", -1)),
                            },
                        }
                    )
            
            # Clean up old violations if person no longer in restricted zone
            current_violations = {(int(obj.get("object_id", -1)), str((obj.get("zones", [""])[0]) if obj.get("restricted_zone_alert") else ""))
                                  for obj in event.get("objects", []) if obj.get("restricted_zone_alert")}
            violations_to_remove = [v for v in _restricted_zone_violations if v not in current_violations and v[1]]
            for v in violations_to_remove:
                _restricted_zone_violations.discard(v)
        except Exception as e:
            logger.error("Error processing restricted_zone alerts: %s", e, exc_info=True)

        event_id = str(event.get("event_id") or uuid4())
        event["event_id"] = event_id
        event_publisher: EventPublisher = app.state.event_publisher
        
        try:
            await event_publisher.publish(event)
        except Exception as e:
            logger.error("Error publishing event: %s", e, exc_info=True)

        # Publish analytics results for all raw alerts
        try:
            for raw_alert in raw_alerts:
                metadata = raw_alert.get("metadata", {})
                await analytics_result_publisher.publish(
                    {
                        "event_id": event_id,
                        "detector_type": str(raw_alert.get("alert_type", "")),
                        "confidence": float(metadata.get("confidence", 0.0)),
                        "metadata": {
                            "alert_type": str(raw_alert.get("alert_type", "")),
                            "object_id": int(raw_alert.get("object_id", -1)),
                            "class_name": str(raw_alert.get("class_name", "unknown")),
                            "zone": str(raw_alert.get("zone", "")),
                            "dwell_seconds": float(metadata.get("dwell_seconds", 0.0)),
                            "person_count": int(metadata.get("person_count", 0)),
                            "frame_id": int(metadata.get("frame_id", event.get("frame_id", -1))),
                        },
                    }
                )
        except Exception as e:
            logger.error("Error publishing analytics results: %s", e, exc_info=True)

        # Process through alert engine
        try:
            finalized_alerts = await alert_engine.process(raw_alerts, event, frame)
        except Exception as e:
            logger.error("Error in alert_engine.process: %s", e, exc_info=True)
            finalized_alerts = []

        # Publish finalized alerts
        try:
            for alert in finalized_alerts:
                try:
                    await alert_publisher.publish(alert)
                except Exception as e:
                    logger.error("Error publishing alert: %s", e, exc_info=True)
                
                try:
                    await firebase_notifier.notify(alert)
                except Exception as e:
                    logger.error("Error sending Firebase notification: %s", e, exc_info=True)
                
                try:
                    await ws_manager.broadcast(alert)
                except Exception as e:
                    logger.error("Error broadcasting alert: %s", e, exc_info=True)
        except Exception as e:
            logger.error("Error processing finalized alerts: %s", e, exc_info=True)

        return {"status": "ok", "alerts_generated": len(finalized_alerts)}
    except Exception as e:
        logger.error("Unhandled error in receive_event: %s", e, exc_info=True)
        return {"status": "error", "detail": str(e)}


@app.websocket("/ws/analytics")
async def analytics_ws(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming finalized alerts to clients."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.ANALYTICS_HOST, port=config.ANALYTICS_PORT)
