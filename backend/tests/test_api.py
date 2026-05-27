from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def get_tokens() -> tuple[str, str]:
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    return data["access_token"], data["refresh_token"]


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_and_refresh() -> None:
    _, refresh = get_tokens()
    response = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_event_and_alert_flow() -> None:
    access, _ = get_tokens()
    event_payload = {
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
    assert client.post("/events", json=event_payload).status_code == 200
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
    assert client.post("/alerts", json=alert_payload).status_code == 200
    alerts_resp = client.get("/alerts", headers={"Authorization": f"Bearer {access}"})
    assert alerts_resp.status_code == 200
    assert len(alerts_resp.json()) >= 1
