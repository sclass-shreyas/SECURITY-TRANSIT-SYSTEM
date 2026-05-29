from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database.transactions import transactional
from backend.models.event import Event
from backend.repositories import CameraRepository, EventRepository
from backend.schemas.event import EventIn


def _settings_for_session(db: AsyncSession):
    return db.info.get("settings") or get_settings()


async def create_event(db: AsyncSession, payload: EventIn) -> Event:
    settings = _settings_for_session(db)
    event_repo = EventRepository(db)
    camera_repo = CameraRepository(db)

    async with transactional(db):
        camera = await camera_repo.ensure_default_camera(settings) if payload.camera_id is None else await camera_repo.ensure_camera(
            payload.camera_id, camera_name=f"camera-{payload.camera_id}"
        )
        event = Event(
            event_id=payload.event_id or uuid4(),
            correlation_id=payload.correlation_id or payload.event_id,
            schema_version=payload.schema_version,
            camera_id=camera.camera_id,
            frame_id=payload.frame_id,
            timestamp=payload.timestamp,
            raw_payload=payload.model_dump(mode="json"),
        )
        return await event_repo.add(event)
