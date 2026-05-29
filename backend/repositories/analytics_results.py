from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from backend.models.analytics_result import AnalyticsResult
from backend.repositories.base import BaseRepository


class AnalyticsResultRepository(BaseRepository[AnalyticsResult]):
    model = AnalyticsResult
    identity_column = AnalyticsResult.result_id

    async def list_by_event_id(self, event_id: UUID) -> list[AnalyticsResult]:
        result = await self.session.execute(select(AnalyticsResult).where(AnalyticsResult.event_id == event_id))
        return list(result.scalars().all())
