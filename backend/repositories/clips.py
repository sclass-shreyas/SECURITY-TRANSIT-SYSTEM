from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from backend.models.clip import Clip
from backend.repositories.base import BaseRepository


class ClipRepository(BaseRepository[Clip]):
    model = Clip
    identity_column = Clip.id

    async def get_by_alert_id(self, alert_id: UUID) -> Clip | None:
        result = await self.session.execute(select(Clip).where(Clip.alert_id == alert_id))
        return result.scalar_one_or_none()
