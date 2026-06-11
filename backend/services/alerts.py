from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database.transactions import transactional
from backend.models.alert import Alert
from backend.models.clip import Clip
from backend.models.event import Event
from backend.repositories import AlertRepository, CameraRepository, ClipRepository, EventRepository
from backend.schemas.alert import AlertIn, AlertOut


def _settings_for_session(db: AsyncSession):
    return db.info.get("settings") or get_settings()


def alert_to_out(alert: Alert) -> AlertOut:
    return AlertOut(
        alert_id=alert.alert_id,
        event_id=alert.event_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        timestamp=alert.created_at,
        resolved_at=alert.resolved_at,
        object_id=alert.object_id,
        class_name=alert.class_name,
        zone=alert.zone,
        clip_path=alert.clip_path,
        metadata=alert.metadata_json,
    )


async def _resolve_event_for_alert(
    *,
    event_repo: EventRepository,
    camera_repo: CameraRepository,
    settings,
    payload: AlertIn,
) -> Event:
    camera = await camera_repo.ensure_default_camera(settings)
    metadata = payload.metadata.model_dump() if hasattr(payload.metadata, "model_dump") else dict(payload.metadata)
    if payload.event_id is not None:
        existing = await event_repo.get_by_id(payload.event_id)
        if existing is not None:
            return existing

    frame_id = int(metadata.get("frame_id", 0))
    matched = await event_repo.find_by_frame_timestamp(
        camera_id=camera.camera_id,
        frame_id=frame_id,
        timestamp=payload.timestamp,
    )
    if matched is not None:
        return matched

    synthetic_event = Event(
        event_id=uuid4(),
        correlation_id=uuid4(),
        schema_version="1.0",
        camera_id=camera.camera_id,
        frame_id=frame_id,
        timestamp=payload.timestamp,
        raw_payload=payload.model_dump(mode="json"),
    )
    return await event_repo.add(synthetic_event)


async def create_alert(db: AsyncSession, payload: AlertIn) -> Alert:
    settings = _settings_for_session(db)
    alert_repo = AlertRepository(db)
    clip_repo = ClipRepository(db)
    event_repo = EventRepository(db)
    camera_repo = CameraRepository(db)

    async with transactional(db):
        metadata = payload.metadata.model_dump() if hasattr(payload.metadata, "model_dump") else dict(payload.metadata)
        event = await _resolve_event_for_alert(
            event_repo=event_repo,
            camera_repo=camera_repo,
            settings=settings,
            payload=payload,
        )

        alert = Alert(
            alert_id=payload.alert_id or uuid4(),
            event_id=event.event_id,
            alert_type=payload.alert_type,
            severity=payload.severity,
            status=payload.status,
            created_at=payload.timestamp,
            resolved_at=payload.resolved_at,
            object_id=payload.object_id,
            class_name=payload.class_name,
            zone=payload.zone,
            clip_path=payload.clip_path,
            metadata_json=metadata,
        )
        await alert_repo.add(alert)
        if payload.clip_path:
            await clip_repo.add(Clip(alert_id=alert.alert_id, clip_path=payload.clip_path))
        return alert


async def get_alert(db: AsyncSession, alert_id) -> Alert | None:
    return await AlertRepository(db).get_by_id(alert_id)


async def list_alerts(
    db: AsyncSession,
    severity: str | None = None,
    limit: int = 100,
) -> list[AlertOut]:
    alerts = await AlertRepository(db).list_alerts(severity=severity, limit=limit)
    return [alert_to_out(alert) for alert in alerts]
