from __future__ import annotations

from sqlalchemy import select

from backend.models.zone import Zone
from backend.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[Zone]):
    model = Zone
    identity_column = Zone.id

    async def get_by_name(self, zone_name: str) -> Zone | None:
        result = await self.session.execute(select(Zone).where(Zone.zone_name == zone_name))
        return result.scalar_one_or_none()
