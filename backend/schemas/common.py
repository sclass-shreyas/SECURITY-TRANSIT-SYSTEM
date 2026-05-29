from __future__ import annotations

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Simple message response body."""

    message: str
