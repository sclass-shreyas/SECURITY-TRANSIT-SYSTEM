from __future__ import annotations

import pytest
from uuid import uuid4

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_detection_event_and_analytics_alert_flow_update_stats(client: AsyncClient) -> None:
    event_payload = {
        "event_id": str(uuid4()),
        "frame_id": 7,
        "timestamp": "2026-05-26T10:00:00Z",
        "objects": [
            {
                "object_id": 101,
                "class_name": "person",
                "confidence": 0.91,
                "bbox": [10, 20, 100, 200],
                "centroid": [55, 110],
                "zones": ["Zone-A"],
                "dwell_seconds": 12.5,
                "restricted_zone_alert": True,
            },
            {
                "object_id": 202,
                "class_name": "backpack",
                "confidence": 0.77,
                "bbox": [120, 130, 180, 220],
                "centroid": [150, 175],
                "zones": [],
                "dwell_seconds": 2.0,
                "restricted_zone_alert": False,
            },
        ],
    }

    alert_payload = {
        "alert_id": "11111111-1111-4111-8111-111111111111",
        "alert_type": "restricted_zone",
        "severity": "high",
        "timestamp": "2026-05-26T10:00:05Z",
        "object_id": 101,
        "class_name": "person",
        "zone": "Zone-A",
        "clip_path": "clips/alert.avi",
        "metadata": {"dwell_seconds": 12.5, "person_count": 1, "confidence": 0.91, "frame_id": 7},
    }

    event_response = await client.post("/api/v1/events", json=event_payload)
    assert event_response.status_code == 200

    analytics_result_payload = {
        "event_id": event_payload["event_id"],
        "detector_type": "restricted_zone",
        "confidence": 0.91,
        "metadata": {
            "alert_type": "restricted_zone",
            "object_id": 101,
            "class_name": "person",
            "zone": "Zone-A",
            "dwell_seconds": 12.5,
            "person_count": 1,
            "frame_id": 7,
        },
    }

    result_response = await client.post("/api/v1/analytics-results/", json=analytics_result_payload)
    assert result_response.status_code == 200
    assert result_response.json() == {"message": "analytics result stored"}

    alert_response = await client.post("/api/v1/alerts", json=alert_payload)
    assert alert_response.status_code == 200

    stats_response = await client.get("/api/v1/stats/")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_events"] == 1
    assert stats["total_alerts"] == 1
    assert stats["high_severity_count"] == 1
    assert stats["by_type"]["restricted_zone"] == 1
    assert stats["by_severity"]["high"] == 1
    assert stats["most_active_zone"] == "Zone-A"

    results_response = await client.get("/api/v1/analytics-results/?event_id=" + event_payload["event_id"])
    assert results_response.status_code == 200
    results = results_response.json()
    assert len(results) == 1
    assert results[0]["detector_type"] == "restricted_zone"
