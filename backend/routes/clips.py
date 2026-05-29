from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from backend.models import Clip

router = APIRouter(prefix="/api/v1/clips", tags=["clips"])


def _clip_to_dict(clip: Clip) -> dict[str, Any]:
    """Serialize a clip ORM row to an API dictionary."""
    created_at: datetime = clip.created_at
    return {
        "id": clip.id,
        "alert_id": clip.alert_id,
        "file_path": clip.file_path,
        "duration_seconds": clip.duration_seconds,
        "created_at": created_at,
    }


@router.get("/")
async def list_clips(request: Request) -> list[dict[str, Any]]:
    """List all stored alert clips."""
    async with request.app.state.sessionmaker() as session:
        rows = (await session.scalars(select(Clip).order_by(Clip.created_at.desc()))).all()
    return [_clip_to_dict(row) for row in rows]


@router.get("/{alert_id}")
async def get_clip(alert_id: str, request: Request) -> dict[str, Any]:
    """Return the clip associated with an alert ID."""
    async with request.app.state.sessionmaker() as session:
        row = await session.scalar(select(Clip).where(Clip.alert_id == alert_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    return _clip_to_dict(row)
