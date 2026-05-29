from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.transactions import transactional
from backend.models.analytics_result import AnalyticsResult
from backend.repositories import AnalyticsResultRepository
from backend.schemas.analytics_result import AnalyticsResultIn


async def record_analytics_result(db: AsyncSession, payload: AnalyticsResultIn) -> AnalyticsResult:
    repo = AnalyticsResultRepository(db)
    async with transactional(db):
        result = AnalyticsResult(
            result_id=payload.result_id,
            event_id=payload.event_id,
            detector_type=payload.detector_type,
            confidence=payload.confidence,
            metadata_json=payload.metadata,
        )
        return await repo.add(result)
