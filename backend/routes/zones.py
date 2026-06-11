from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from backend.models.zone import Zone
from backend.schemas.common import MessageResponse
from backend.schemas.zone import ZoneIn, ZoneOut

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@router.get("/", response_model=list[ZoneOut])
async def list_zones(request: Request) -> list[ZoneOut]:
    """List all configured zones."""
    async with request.app.state.sessionmaker() as session:
        result = await session.execute(select(Zone).order_by(Zone.zone_id))
        rows = result.scalars().all()
    return [ZoneOut.model_validate(row) for row in rows]


@router.post("/", response_model=ZoneOut)
async def create_zone(zone: ZoneIn, request: Request) -> ZoneOut:
    """Create a new transit zone."""
    async with request.app.state.sessionmaker() as session:
        row = Zone(
            zone_id=zone.zone_id,
            name=zone.name,
            restricted=zone.restricted,
            zone_name=zone.zone_name,
            polygon_points_json=zone.polygon_points_json or zone.polygon or [],
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return ZoneOut.model_validate(row)


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(zone_id: str, request: Request) -> ZoneOut:
    """Return one zone by its external zone ID."""
    async with request.app.state.sessionmaker() as session:
        result = await session.execute(select(Zone).where(Zone.zone_id == zone_id))
        row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return ZoneOut.model_validate(row)


@router.delete("/{zone_id}", response_model=MessageResponse)
async def delete_zone(zone_id: str, request: Request) -> MessageResponse:
    """Delete one zone by its external zone ID."""
    async with request.app.state.sessionmaker() as session:
        row = await session.scalar(select(Zone).where(Zone.zone_id == zone_id))
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
        await session.delete(row)
        await session.commit()
    return MessageResponse(message="ok")
