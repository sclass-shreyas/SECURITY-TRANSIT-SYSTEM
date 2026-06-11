from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.database.types import JSONBType


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (
        Index("ix_zones_zone_id", "zone_id", unique=True),
        Index("ix_zones_zone_name", "zone_name", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    restricted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    zone_name: Mapped[str] = mapped_column(String(120), nullable=False)
    polygon_points_json: Mapped[list[list[int]]] = mapped_column(JSONBType(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
