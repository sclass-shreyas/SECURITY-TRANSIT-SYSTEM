from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.types import GUID, JSONBType


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_event_id", "event_id"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_metadata_gin", "metadata", postgresql_using="gin"),
    )

    alert_id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    object_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False, default=0)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    clip_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONBType(), nullable=False, default=dict)

    event = relationship("Event", back_populates="alerts")
    clips = relationship("Clip", back_populates="alert", cascade="all, delete-orphan")

    @property
    def timestamp(self) -> datetime:
        return self.created_at

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        self.created_at = value
