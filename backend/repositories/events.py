from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from backend.models.event import Event
from backend.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event
    identity_column = Event.event_id

    async def find_by_frame_timestamp(
        self,
        *,
        camera_id: UUID,
        frame_id: int,
        timestamp: datetime,
    ) -> Event | None:
        result = await self.session.execute(
            select(Event)
            .where(Event.camera_id == camera_id, Event.frame_id == frame_id, Event.timestamp == timestamp)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_by_frame(
        self,
        *,
        camera_id: UUID,
        frame_id: int,
    ) -> Event | None:
        result = await self.session.execute(
            select(Event)
            .where(Event.camera_id == camera_id, Event.frame_id == frame_id)
            .order_by(Event.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
