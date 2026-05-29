from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.models.camera import Camera
from backend.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    model = Camera
    identity_column = Camera.camera_id

    async def get_by_name(self, camera_name: str) -> Camera | None:
        result = await self.session.execute(select(Camera).where(Camera.camera_name == camera_name))
        return result.scalar_one_or_none()

    async def ensure_default_camera(self, settings: Settings) -> Camera:
        camera = await self.get_by_id(settings.DEFAULT_CAMERA_ID)
        if camera is not None:
            return camera

        camera = Camera(
            camera_id=settings.DEFAULT_CAMERA_ID,
            camera_name="default-camera",
            location="unspecified",
            is_active=True,
            metadata_json={"managed_by": "bootstrap"},
        )
        return await self.add(camera)

    async def ensure_camera(
        self,
        camera_id: UUID,
        camera_name: str = "default-camera",
        location: str | None = None,
        metadata: dict | None = None,
    ) -> Camera:
        camera = await self.get_by_id(camera_id)
        if camera is not None:
            return camera
        camera = Camera(
            camera_id=camera_id,
            camera_name=camera_name,
            location=location,
            metadata_json=metadata or {},
            is_active=True,
        )
        return await self.add(camera)
