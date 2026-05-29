from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select

from backend.models.alert import Alert
from backend.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert
    identity_column = Alert.alert_id

    async def list_alerts(self, *, severity: str | None = None, limit: int = 100) -> list[Alert]:
        stmt = select(Alert)
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        stmt = stmt.order_by(desc(Alert.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_event_id(self, event_id: UUID) -> Alert | None:
        result = await self.session.execute(select(Alert).where(Alert.event_id == event_id))
        return result.scalar_one_or_none()
