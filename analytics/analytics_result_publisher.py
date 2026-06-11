"""Analytics result publisher for forwarding detector outputs to the backend."""

from __future__ import annotations

import logging
from typing import Any

import httpx

import config


class AnalyticsResultPublisher:
    """Publish detector outputs to the backend analytics-result endpoint."""

    def __init__(self) -> None:
        """Initialize async HTTP client for outbound result posting."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = httpx.AsyncClient(timeout=config.POST_TIMEOUT_SECONDS)

    async def publish(self, result: dict[str, Any]) -> None:
        """POST one analytics result to the backend."""
        try:
            response = await self.client.post(config.P3_ANALYTICS_RESULTS_ENDPOINT, json=result)
            if response.status_code != 200:
                self.logger.warning(
                    "Non-200 response from analytics result backend: status=%s body=%s",
                    response.status_code,
                    response.text,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            self.logger.warning("Analytics result publish failed but processing continues: %s", exc)

    async def close(self) -> None:
        """Close HTTP resources."""
        await self.client.aclose()
