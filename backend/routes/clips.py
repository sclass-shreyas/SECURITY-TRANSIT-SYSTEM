from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.deps import get_db
from backend.services.alerts import get_alert

router = APIRouter(prefix="/api/v1", tags=["clips"])


@router.get("/clips/{alert_id}")
async def read_clip(
    alert_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    alert = await get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    clip_name = alert.clip_path or f"{alert.alert_id}.mp4"
    clip_path = Path(clip_name)
    clip_file = clip_path if clip_path.is_absolute() else (Path(request.app.state.settings.CLIPS_BASE_DIR) / clip_path).resolve()
    if not clip_file.exists() or not clip_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    return FileResponse(path=str(clip_file), media_type="video/mp4")
