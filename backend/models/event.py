from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.types import GUID, JSONBType


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_correlation_id", "correlation_id"),
        Index("ix_events_camera_id", "camera_id"),
        Index("ix_events_timestamp", "timestamp"),
        Index("ix_events_raw_payload_gin", "raw_payload", postgresql_using="gin"),
    )

    event_id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    correlation_id: Mapped[UUID] = mapped_column(GUID(), nullable=False, default=uuid4)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    camera_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("cameras.camera_id", ondelete="RESTRICT"), nullable=False
    )
    frame_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONBType(), nullable=False)

    camera = relationship("Camera", back_populates="events")
    alerts = relationship("Alert", back_populates="event", cascade="all, delete-orphan")
    analytics_results = relationship("AnalyticsResult", back_populates="event", cascade="all, delete-orphan")

    @property
    def raw_json(self) -> dict[str, Any]:
        return self.raw_payload

    @raw_json.setter
    def raw_json(self, value: dict[str, Any]) -> None:
        self.raw_payload = value
