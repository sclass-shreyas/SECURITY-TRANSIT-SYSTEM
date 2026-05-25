"""FastAPI entry point for analytics, alerts, and real-time alert streaming."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect

import config
from alert_engine import AlertEngine
from alert_publisher import AlertPublisher
from crowd_density import CrowdDensityDetector
from firebase_notifier import FirebaseNotifier
from loitering_detector import LoiteringDetector
from theft_detector import TheftDetector
from unattended_object import UnattendedObjectDetector

app = FastAPI(title="Smart Transit Analytics")
logger = logging.getLogger("analytics.main")


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
    app.state.firebase_notifier = FirebaseNotifier()
    app.state.alert_publisher = AlertPublisher()
    app.state.latest_frame = np.empty((0, 0, 3), dtype=np.uint8)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Release outbound publisher resources."""
    publisher: AlertPublisher = app.state.alert_publisher
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
    loitering_detector: LoiteringDetector = app.state.loitering_detector
    crowd_density: CrowdDensityDetector = app.state.crowd_density
    unattended_object: UnattendedObjectDetector = app.state.unattended_object
    theft_detector: TheftDetector = app.state.theft_detector
    alert_engine: AlertEngine = app.state.alert_engine
    firebase_notifier: FirebaseNotifier = app.state.firebase_notifier
    alert_publisher: AlertPublisher = app.state.alert_publisher

    frame = app.state.latest_frame
    raw_alerts: list[dict[str, Any]] = []

    raw_alerts.extend(loitering_detector.analyze(event))
    raw_alerts.extend(crowd_density.analyze(event))
    raw_alerts.extend(unattended_object.analyze(event))
    raw_alerts.extend(theft_detector.analyze(frame, event))

    for obj in event.get("objects", []):
        if obj.get("restricted_zone_alert"):
            zones = obj.get("zones", [""])
            raw_alerts.append(
                {
                    "alert_type": "restricted_zone",
                    "object_id": int(obj.get("object_id", -1)),
                    "class_name": str(obj.get("class_name", "unknown")),
                    "zone": str(zones[0] if zones else ""),
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

    finalized_alerts = await alert_engine.process(raw_alerts, event, frame)

    for alert in finalized_alerts:
        await alert_publisher.publish(alert)
        await firebase_notifier.notify(alert)
        await ws_manager.broadcast(alert)

    return {"status": "ok", "alerts_generated": len(finalized_alerts)}


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
