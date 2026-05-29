from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.database.types import JSONBType


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (Index("ix_zones_zone_name", "zone_name", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    polygon_points_json: Mapped[list[list[int]]] = mapped_column(JSONBType(), nullable=False)
