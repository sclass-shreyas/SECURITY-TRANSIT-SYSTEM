"""Tests for crowd density detector."""

from __future__ import annotations

from crowd_density import CrowdDensityDetector


def _person(object_id: int, zone: str) -> dict:
    return {
        "object_id": object_id,
        "class_name": "person",
        "confidence": 0.8,
        "bbox": [0, 0, 10, 10],
        "centroid": [5, 5],
        "zones": [zone] if zone else [],
        "dwell_seconds": 0.0,
        "restricted_zone_alert": False,
    }


def test_below_threshold_generates_no_alert() -> None:
    detector = CrowdDensityDetector()
    event = {"frame_id": 1, "objects": [_person(i, "zone_1") for i in range(5)]}
    assert detector.analyze(event) == []


def test_above_threshold_generates_alert() -> None:
    detector = CrowdDensityDetector()
    event = {"frame_id": 1, "objects": [_person(i, "zone_1") for i in range(7)]}
    alerts = detector.analyze(event)
    assert any(a["alert_type"] == "crowd_surge" for a in alerts)


def test_zone_specific_counting() -> None:
    detector = CrowdDensityDetector()
    objs = [_person(i, "zone_1") for i in range(6)] + [_person(100 + i, "zone_2") for i in range(2)]
    alerts = detector.analyze({"frame_id": 2, "objects": objs})
    zone_alerts = [a for a in alerts if a["zone"] == "zone_1"]
    assert len(zone_alerts) >= 1


def test_person_count_metadata_correct() -> None:
    detector = CrowdDensityDetector()
    event = {"frame_id": 1, "objects": [_person(i, "zone_1") for i in range(8)]}
    alerts = detector.analyze(event)
    assert any(a["metadata"]["person_count"] == 8 for a in alerts)
