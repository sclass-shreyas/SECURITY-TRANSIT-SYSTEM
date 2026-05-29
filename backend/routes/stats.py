from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.deps import get_db
from backend.schemas.stats import StatsSummary, TimelinePoint
from backend.services.stats import get_stats_summary, get_timeline

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("", response_model=StatsSummary)
@router.get("/summary", response_model=StatsSummary)
async def stats_summary(db: AsyncSession = Depends(get_db)) -> StatsSummary:
    return await get_stats_summary(db)


@router.get("/timeline", response_model=list[TimelinePoint])
async def stats_timeline(db: AsyncSession = Depends(get_db)) -> list[TimelinePoint]:
    return await get_timeline(db)
