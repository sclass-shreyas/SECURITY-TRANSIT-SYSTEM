from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: str
    ready: bool
    database: str
