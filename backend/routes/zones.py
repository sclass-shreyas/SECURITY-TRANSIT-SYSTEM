from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.deps import get_db
from backend.schemas.common import MessageResponse
from backend.schemas.zone import ZoneIn, ZoneOut
from backend.services.zones import create_zone, delete_zone, get_zone, list_zones, update_zone

router = APIRouter(prefix="/api/v1", tags=["zones"])


@router.get("/zones", response_model=list[ZoneOut])
async def read_zones(db: AsyncSession = Depends(get_db)) -> list[ZoneOut]:
    return await list_zones(db)


@router.post("/zones", response_model=ZoneOut)
async def add_zone(payload: ZoneIn, db: AsyncSession = Depends(get_db)) -> ZoneOut:
    zone = await create_zone(db, payload)
    return ZoneOut.model_validate(zone)


@router.put("/zones/{zone_id}", response_model=ZoneOut)
async def edit_zone(zone_id: int, payload: ZoneIn, db: AsyncSession = Depends(get_db)) -> ZoneOut:
    zone = await get_zone(db, zone_id)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    zone = await update_zone(db, zone, payload)
    return ZoneOut.model_validate(zone)


@router.delete("/zones/{zone_id}", response_model=MessageResponse)
async def remove_zone(zone_id: int, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    zone = await get_zone(db, zone_id)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    await delete_zone(db, zone)
    return MessageResponse(message="zone deleted")
