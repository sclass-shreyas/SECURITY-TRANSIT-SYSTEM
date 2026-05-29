from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from backend.models import AnalyticsResult, Alert, Camera, Event
from backend.repositories import CameraRepository
from backend.schemas.alert import AlertIn
from backend.schemas.event import EventIn
from backend.services.alerts import create_alert
from backend.services.events import create_event


def test_postgresql_schema_uses_uuid_and_jsonb() -> None:
    event_sql = str(CreateTable(Event.__table__).compile(dialect=postgresql.dialect()))
    alert_sql = str(CreateTable(Alert.__table__).compile(dialect=postgresql.dialect()))
    analytics_sql = str(CreateTable(AnalyticsResult.__table__).compile(dialect=postgresql.dialect()))
    camera_sql = str(CreateTable(Camera.__table__).compile(dialect=postgresql.dialect()))

    assert "UUID" in event_sql
    assert "JSONB" in event_sql
    assert "FOREIGN KEY" in event_sql

    assert "UUID" in alert_sql
    assert "JSONB" in alert_sql
    assert "FOREIGN KEY" in alert_sql

    assert "JSONB" in analytics_sql
    assert "UUID" in analytics_sql
    assert "JSONB" in camera_sql


@pytest.mark.asyncio
async def test_event_and_alert_services_persist_related_rows(app) -> None:
    async with app.state.sessionmaker() as session:
        session.info["settings"] = app.state.settings
        await create_event(
            session,
            EventIn(
                frame_id=42,
                timestamp=datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc),
                objects=[],
            ),
        )

        alert = await create_alert(
            session,
            AlertIn(
                alert_id=uuid4(),
                alert_type="loitering",
                severity="high",
                timestamp=datetime(2026, 5, 29, 12, 0, 5, tzinfo=timezone.utc),
                object_id=7,
                class_name="person",
                zone="Zone-A",
                clip_path="camera-1.mp4",
                metadata={"frame_id": 42},
            ),
        )

        assert alert.status == "open"
        assert len(session.store.cameras) == 1
        assert len(session.store.events) == 2
        assert len(session.store.alerts) == 1
        assert len(session.store.clips) == 1
        assert alert.event_id in {event.event_id for event in session.store.events}

        camera_repo = CameraRepository(session)
        default_camera = await camera_repo.ensure_default_camera(app.state.settings)
        assert default_camera.camera_id == app.state.settings.DEFAULT_CAMERA_ID
