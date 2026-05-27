from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.zone import Zone
from app.schemas.common import MessageResponse
from app.schemas.zone import ZoneIn, ZoneOut

router = APIRouter(tags=["zones"])


@router.get("/zones", response_model=list[ZoneOut])
async def get_zones(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ZoneOut]:
    result = await db.execute(select(Zone).order_by(Zone.id))
    return [ZoneOut.model_validate(z) for z in result.scalars().all()]


@router.post("/zones", response_model=ZoneOut)
async def create_zone(
    payload: ZoneIn,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ZoneOut:
    zone = Zone(zone_name=payload.zone_name, polygon_points_json=payload.polygon_points_json)
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return ZoneOut.model_validate(zone)


@router.put("/zones/{zone_id}", response_model=ZoneOut)
async def update_zone(
    zone_id: int,
    payload: ZoneIn,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ZoneOut:
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    zone.zone_name = payload.zone_name
    zone.polygon_points_json = payload.polygon_points_json
    await db.commit()
    await db.refresh(zone)
    return ZoneOut.model_validate(zone)


@router.delete("/zones/{zone_id}", response_model=MessageResponse)
async def delete_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> MessageResponse:
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    await db.delete(zone)
    await db.commit()
    return MessageResponse(message="zone deleted")
