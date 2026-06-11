from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import init_db
from backend.models.zone import Zone
from backend.repositories.cameras import CameraRepository

logger = logging.getLogger(__name__)


async def ensure_default_camera(session: AsyncSession) -> None:
    """Seed the default camera and configured zones when the database is empty."""
    settings = session.info.get("settings")
    if settings is None:
        raise RuntimeError("Session is missing application settings")

    bind = session.bind
    if bind is None:
        raise RuntimeError("AsyncSession is not bound to an engine")
    if getattr(bind.dialect, "name", "") != "postgresql":
        await init_db(bind)

    camera_repo = CameraRepository(session)
    await camera_repo.ensure_default_camera(settings)

    existing_zone = await session.scalar(select(Zone.id).limit(1))
    if existing_zone is not None:
        return

    zones_path = Path(__file__).resolve().parents[2] / "detection" / "zones.json"
    if not zones_path.exists():
        logger.warning("Default zones file not found: %s", zones_path)
        return

    zones_payload = json.loads(zones_path.read_text(encoding="utf-8"))
    for zone_data in zones_payload.get("zones", []):
        zone_id = zone_data.get("zone_id") or zone_data.get("id")
        if not zone_id:
            logger.warning("Skipping zone without id: %s", zone_data)
            continue
        session.add(
            Zone(
                zone_id=zone_id,
                name=zone_data["name"],
                restricted=bool(zone_data.get("restricted", False)),
                zone_name=str(zone_data["name"]),
                polygon_points_json=zone_data.get("polygon", []),
            )
        )
    await session.commit()
