from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.clip import Clip
from app.models.event import Event
from app.schemas.alert import AlertIn
from app.schemas.event import EventIn


async def store_event(db: AsyncSession, payload: EventIn) -> Event:
    event = Event(frame_id=payload.frame_id, timestamp=payload.timestamp, raw_json=payload.model_dump(mode="json"))
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def store_alert(db: AsyncSession, payload: AlertIn) -> Alert:
    alert = Alert(
        alert_id=payload.alert_id,
        alert_type=payload.alert_type,
        severity=payload.severity,
        timestamp=payload.timestamp,
        object_id=payload.object_id,
        class_name=payload.class_name,
        zone=payload.zone,
        clip_path=payload.clip_path,
        metadata_json=payload.metadata.model_dump(mode="json"),
    )
    db.add(alert)
    existing_clip = await db.execute(select(Clip).where(Clip.alert_id == payload.alert_id))
    if existing_clip.scalar_one_or_none() is None:
        db.add(Clip(alert_id=payload.alert_id, clip_path=payload.clip_path))
    await db.commit()
    await db.refresh(alert)
    return alert


async def get_alert_counts_by_severity(db: AsyncSession) -> dict[str, int]:
    rows = await db.execute(select(Alert.severity, func.count(Alert.alert_id)).group_by(Alert.severity))
    return {severity: count for severity, count in rows.all()}


def resolve_clip_path(base_dir: str, clip_path: str) -> Path:
    clip = Path(clip_path)
    if clip.is_absolute():
        return clip
    return (Path(base_dir) / clip).resolve()
