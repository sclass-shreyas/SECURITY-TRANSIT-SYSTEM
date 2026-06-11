from __future__ import annotations

import sys
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app as create_backend_app
from backend.config import Settings
from backend.database import create_engine_and_sessionmaker
from backend.models.analytics_result import AnalyticsResult
from backend.models.legacy import Alert, Clip, Event, Zone
from backend.services.cameras import ensure_default_camera
import config as analytics_config
from main import app as analytics_app, ws_manager

DETECTION_DIR = ROOT / "detection"
if str(DETECTION_DIR) not in sys.path:
    sys.path.insert(0, str(DETECTION_DIR))

_detection_spec = importlib.util.spec_from_file_location("detection_main_for_e2e", DETECTION_DIR / "main.py")
assert _detection_spec is not None and _detection_spec.loader is not None
_detection_module = importlib.util.module_from_spec(_detection_spec)
sys.modules[_detection_spec.name] = _detection_module
_detection_spec.loader.exec_module(_detection_module)
_build_event = _detection_module._build_event


class StubZoneManager:
    def __init__(self) -> None:
        self.zones = {
            "zone_001": {"restricted": True, "polygon": np.array([[0, 0], [1, 0], [1, 1], [0, 1]])},
        }

    def get_zones_for_object(self, bbox: list[int]) -> list[str]:
        _ = bbox
        return ["zone_001"]

    def update_dwell(self, object_id: int, zones: list[str], timestamp_epoch: float) -> dict[str, float]:
        _ = object_id, timestamp_epoch
        return {zone: 12.5 for zone in zones}


@pytest.mark.asyncio
async def test_end_to_end_detection_to_dashboard_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    backend_db_path = tmp_path / "backend-e2e.db"
    backend_settings = Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{backend_db_path}",
        CLIPS_BASE_DIR=str(tmp_path / "backend-clips"),
    )
    backend_app = create_backend_app(backend_settings)
    engine, sessionmaker = create_engine_and_sessionmaker(backend_settings.DATABASE_URL)
    backend_app.state.settings = backend_settings
    backend_app.state.engine = engine
    backend_app.state.sessionmaker = sessionmaker
    backend_app.state.ready = False

    async with sessionmaker() as session:
        session.info["settings"] = backend_settings
        await ensure_default_camera(session)
    backend_app.state.ready = True

    await analytics_app.router.startup()
    analytics_app.state.latest_frame = np.zeros((64, 64, 3), dtype=np.uint8)

    backend_base_url = "http://backend"
    monkeypatch.setattr(analytics_config, "P3_ALERTS_ENDPOINT", f"{backend_base_url}/api/v1/alerts")
    monkeypatch.setattr(
        analytics_config,
        "P3_ANALYTICS_RESULTS_ENDPOINT",
        f"{backend_base_url}/api/v1/analytics-results",
    )

    backend_transport = ASGITransport(app=backend_app)
    backend_client = AsyncClient(transport=backend_transport, base_url=backend_base_url)
    analytics_app.state.event_publisher.client = backend_client
    analytics_app.state.alert_publisher.client = backend_client
    analytics_app.state.analytics_result_publisher.client = backend_client
    analytics_app.state.firebase_notifier._enabled = False

    try:
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        _, jpeg_bytes = cv2.imencode(".jpg", frame)
        analytics_transport = ASGITransport(app=analytics_app)
        async with AsyncClient(transport=analytics_transport, base_url="http://analytics") as analytics_client:
            frame_response = await analytics_client.post(
                "/frame",
                files={"file": ("frame.jpg", jpeg_bytes.tobytes(), "image/jpeg")},
            )
            assert frame_response.status_code == 200
            assert frame_response.json() == {"status": "ok"}

            detection_event = _build_event(
                frame_id=1,
                tracked_objects=[
                    {
                        "object_id": 101,
                        "class_name": "person",
                        "confidence": 0.95,
                        "bbox": [5, 5, 40, 40],
                    }
                ],
                zone_manager=StubZoneManager(),
                timestamp_epoch=datetime(2026, 5, 26, 10, 0, tzinfo=timezone.utc).timestamp(),
            )

            event_response = await analytics_client.post("/events", json=detection_event)
            assert event_response.status_code == 200
            assert event_response.json()["status"] == "ok"
            assert event_response.json()["alerts_generated"] >= 1

        alerts_response = await backend_client.get("/api/v1/alerts")
        results_response = await backend_client.get("/api/v1/analytics-results")
        clips_response = await backend_client.get("/api/v1/clips/")
        zones_response = await backend_client.get("/api/v1/zones/")
        stats_response = await backend_client.get("/api/v1/stats/")
        dashboard_response = await backend_client.get("/dashboard")

        assert alerts_response.status_code == 200
        assert results_response.status_code == 200
        assert clips_response.status_code == 200
        assert zones_response.status_code == 200
        assert stats_response.status_code == 200
        assert dashboard_response.status_code == 200

        alerts = alerts_response.json()
        results = results_response.json()
        clips = clips_response.json()
        zones = zones_response.json()
        stats = stats_response.json()

        assert len(alerts) >= 1
        assert len(results) >= 1
        assert len(clips) >= 1
        assert len(zones) >= 1
        assert stats["total_alerts"] >= 1
        assert stats["total_events"] >= 1

        async with backend_app.state.sessionmaker() as session:
            persisted_events = (await session.execute(select(Event))).scalars().all()
            persisted_alerts = (await session.execute(select(Alert))).scalars().all()
            persisted_clips = (await session.execute(select(Clip))).scalars().all()
            persisted_results = (await session.execute(select(AnalyticsResult))).scalars().all()
            persisted_zones = (await session.execute(select(Zone))).scalars().all()

        assert persisted_events
        assert persisted_alerts
        assert persisted_clips
        assert persisted_results
        assert persisted_zones
    finally:
        await backend_client.aclose()
        await analytics_app.router.shutdown()
        ws_manager._connections.clear()
