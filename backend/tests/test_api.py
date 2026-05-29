from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_health_and_readiness_endpoints(client: AsyncClient) -> None:
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    health_body = health_response.json()
    assert health_body["status"] == "ok"
    assert health_body["service"] == "Smart Transit Security Backend"
    assert health_body["version"] == "1.0.0"

    ready_response = await client.get("/ready")
    assert ready_response.status_code == 200
    assert ready_response.json() == {"status": "ready", "ready": True, "database": "ok"}

    docs_response = await client.get("/docs")
    assert docs_response.status_code == 200
    assert "Swagger UI" in docs_response.text

    openapi_response = await client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi = openapi_response.json()
    assert "/health" in openapi["paths"]
    assert "/ready" in openapi["paths"]


@pytest.mark.asyncio
async def test_versioned_event_ingest_and_legacy_compatibility(client: AsyncClient) -> None:
    payload = {
        "frame_id": 1,
        "timestamp": "2026-05-26T10:00:00Z",
        "objects": [
            {
                "object_id": 101,
                "class_name": "person",
                "confidence": 0.9,
                "bbox": [10, 20, 100, 200],
                "centroid": [55, 110],
                "zones": ["Zone-A"],
                "dwell_seconds": 5.2,
                "restricted_zone_alert": False,
            }
        ],
    }

    versioned_response = await client.post("/api/v1/events", json=payload)
    assert versioned_response.status_code == 200
    assert versioned_response.json() == {"message": "event stored"}

    legacy_response = await client.post("/events", json=payload)
    assert legacy_response.status_code == 200
    assert legacy_response.json() == {"message": "event stored"}


@pytest.mark.asyncio
async def test_alert_flow_and_validation(client: AsyncClient) -> None:
    alert_payload = {
        "alert_id": "11111111-1111-4111-8111-111111111111",
        "alert_type": "loitering",
        "severity": "high",
        "timestamp": "2026-05-26T10:00:05Z",
        "object_id": 101,
        "class_name": "person",
        "zone": "Zone-A",
        "clip_path": "sample.mp4",
        "metadata": {"dwell_seconds": 5.2, "person_count": 1, "confidence": 0.9, "frame_id": 1},
    }

    ingest_response = await client.post("/api/v1/alerts", json=alert_payload)
    assert ingest_response.status_code == 200
    assert ingest_response.json() == {"message": "alert stored"}

    alerts_response = await client.get("/api/v1/alerts")
    assert alerts_response.status_code == 200
    alerts = alerts_response.json()
    assert len(alerts) == 1
    assert alerts[0]["alert_id"] == alert_payload["alert_id"]

    detail_response = await client.get(f"/api/v1/alerts/{alert_payload['alert_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["zone"] == "Zone-A"

    validation_response = await client.post("/api/v1/events", json={"frame_id": -1, "timestamp": "invalid", "objects": []})
    assert validation_response.status_code == 422


@pytest.mark.asyncio
async def test_frame_upload_endpoint(client: AsyncClient) -> None:
    response = await client.post(
        "/frame",
        files={"frame": ("frame.jpg", b"jpeg-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "frame received"}
