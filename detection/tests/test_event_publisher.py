"""Tests for async event publisher."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from event_publisher import EventPublisher


@pytest.fixture
def sample_event() -> dict:
    """Provide a valid event payload following expected schema."""
    return {
        "frame_id": 1,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "objects": [
            {
                "object_id": 1,
                "class_name": "person",
                "confidence": 0.95,
                "bbox": [10, 20, 30, 40],
                "centroid": [20, 30],
                "zones": ["zone_001"],
                "dwell_seconds": 4.2,
                "restricted_zone_alert": False,
            }
        ],
    }


@pytest.mark.asyncio
@patch("event_publisher.httpx.AsyncClient")
async def test_publish_sends_post_with_correct_json(
    mock_client_cls: MagicMock, sample_event: dict
) -> None:
    """publish should call POST with configured endpoint and event JSON."""
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 200
    client.post.return_value = response
    mock_client_cls.return_value = client

    publisher = EventPublisher()
    await publisher.publish(sample_event)

    client.post.assert_awaited_once()
    args, kwargs = client.post.await_args
    assert kwargs["json"] == sample_event


@pytest.mark.asyncio
@patch("event_publisher.httpx.AsyncClient")
async def test_publish_does_not_raise_on_connection_error(
    mock_client_cls: MagicMock, sample_event: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """publish should swallow connection errors and log warning."""
    client = AsyncMock()
    client.post.side_effect = httpx.ConnectError("boom")
    mock_client_cls.return_value = client

    publisher = EventPublisher()
    await publisher.publish(sample_event)

    assert "Event publish failed but loop continues" in caplog.text


@pytest.mark.asyncio
@patch("event_publisher.httpx.AsyncClient")
async def test_publish_does_not_raise_on_timeout(
    mock_client_cls: MagicMock, sample_event: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """publish should swallow timeout exceptions and log warning."""
    client = AsyncMock()
    client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client_cls.return_value = client

    publisher = EventPublisher()
    await publisher.publish(sample_event)

    assert "Event publish failed but loop continues" in caplog.text


def test_event_schema_contains_required_keys(sample_event: dict) -> None:
    """Event payload should contain all required top-level and object keys."""
    assert set(sample_event.keys()) == {"frame_id", "timestamp", "objects"}
    assert len(sample_event["objects"]) == 1
    assert set(sample_event["objects"][0].keys()) == {
        "object_id",
        "class_name",
        "confidence",
        "bbox",
        "centroid",
        "zones",
        "dwell_seconds",
        "restricted_zone_alert",
    }
