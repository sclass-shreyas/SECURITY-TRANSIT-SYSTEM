from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User

router = APIRouter(tags=["clips"])
settings = get_settings()


@router.get("/clips/{alert_id}")
async def get_clip(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> FileResponse:
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    clip_name = alert.clip_path or f"{alert.alert_id}.mp4"
    clip_path = Path(clip_name)
    clip_file = (
        clip_path
        if clip_path.is_absolute()
        else (Path(settings.CLIPS_BASE_DIR) / clip_path).resolve()
    )
    if not clip_file.exists() or not clip_file.is_file():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(path=str(clip_file), media_type="video/mp4")
