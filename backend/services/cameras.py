from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.repositories import CameraRepository


async def ensure_default_camera(db: AsyncSession):
    settings = db.info.get("settings") or get_settings()
    return await CameraRepository(db).ensure_default_camera(settings)
