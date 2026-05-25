"""Async event publisher for posting detection events to the backend API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

import config


class EventPublisher:
    """Publish structured detection events via async HTTP POST."""

    def __init__(self) -> None:
        """Initialize async HTTP client."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = httpx.AsyncClient(timeout=config.POST_TIMEOUT_SECONDS)

    async def publish(self, event: dict[str, Any]) -> None:
        """POST event JSON to API endpoint with resilient error handling."""
        try:
            response = await self.client.post(config.API_ENDPOINT, json=event)
            if response.status_code != 200:
                self.logger.warning(
                    "Non-200 response from event API: status=%s body=%s",
                    response.status_code,
                    response.text,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            self.logger.warning("Event publish failed but loop continues: %s", exc)

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self.client.aclose()
