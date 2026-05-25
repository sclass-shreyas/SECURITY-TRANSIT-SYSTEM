"""Alert publisher for forwarding finalized alerts to the P3 backend endpoint."""

from __future__ import annotations

import logging
from typing import Any

import httpx

import config


class AlertPublisher:
    """Publish finalized alerts to downstream backend service."""

    def __init__(self) -> None:
        """Initialize async HTTP client for outbound alert posting."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = httpx.AsyncClient(timeout=config.POST_TIMEOUT_SECONDS)

    async def publish(self, alert: dict[str, Any]) -> None:
        """POST one alert to the P3 backend with safe error handling."""
        try:
            response = await self.client.post(config.P3_ALERTS_ENDPOINT, json=alert)
            if response.status_code != 200:
                self.logger.warning(
                    "Non-200 response from alert backend: status=%s body=%s",
                    response.status_code,
                    response.text,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            self.logger.warning("Alert publish failed but processing continues: %s", exc)

    async def close(self) -> None:
        """Close HTTP resources."""
        await self.client.aclose()
