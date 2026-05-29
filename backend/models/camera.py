from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.types import GUID, JSONBType


class Camera(Base):
    __tablename__ = "cameras"
    __table_args__ = (Index("ix_cameras_camera_name", "camera_name", unique=True),)

    camera_id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    camera_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONBType(), nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    events = relationship("Event", back_populates="camera")
