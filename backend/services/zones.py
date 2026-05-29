from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.zone import Zone
from backend.schemas.zone import ZoneIn, ZoneOut


async def list_zones(db: AsyncSession) -> list[ZoneOut]:
    result = await db.execute(select(Zone).order_by(Zone.id))
    return [ZoneOut.model_validate(zone) for zone in result.scalars().all()]


async def get_zone(db: AsyncSession, zone_id: int) -> Zone | None:
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    return result.scalar_one_or_none()


async def create_zone(db: AsyncSession, payload: ZoneIn) -> Zone:
    zone = Zone(zone_name=payload.zone_name, polygon_points_json=payload.polygon_points_json)
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


async def update_zone(db: AsyncSession, zone: Zone, payload: ZoneIn) -> Zone:
    zone.zone_name = payload.zone_name
    zone.polygon_points_json = payload.polygon_points_json
    await db.commit()
    await db.refresh(zone)
    return zone


async def delete_zone(db: AsyncSession, zone: Zone) -> None:
    await db.delete(zone)
    await db.commit()
