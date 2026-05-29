from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.types import GUID, JSONBType


class AnalyticsResult(Base):
    __tablename__ = "analytics_results"
    __table_args__ = (
        Index("ix_analytics_results_event_id", "event_id"),
        Index("ix_analytics_results_detector_type", "detector_type"),
        Index("ix_analytics_results_metadata_gin", "metadata", postgresql_using="gin"),
    )

    result_id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True
    )
    detector_type: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONBType(), nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    event = relationship("Event", back_populates="analytics_results")
