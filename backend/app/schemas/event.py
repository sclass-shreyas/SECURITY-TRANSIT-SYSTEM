from datetime import datetime

from pydantic import BaseModel


class EventIn(BaseModel):
    frame_id: int
    timestamp: datetime
    objects: list[dict]
