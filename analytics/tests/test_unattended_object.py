"""Tests for unattended object detector."""

from __future__ import annotations

from unattended_object import UnattendedObjectDetector


def _event(timestamp: str, objs: list[dict]) -> dict:
    return {"frame_id": 20, "timestamp": timestamp, "objects": objs}


def _person(obj_id: int, centroid: list[int]) -> dict:
    return {
        "object_id": obj_id,
        "class_name": "person",
        "confidence": 0.9,
        "bbox": [0, 0, 10, 10],
        "centroid": centroid,
        "zones": ["zone_1"],
        "dwell_seconds": 0.0,
        "restricted_zone_alert": False,
    }


def _bag(obj_id: int, centroid: list[int]) -> dict:
    return {
        "object_id": obj_id,
        "class_name": "backpack",
        "confidence": 0.9,
        "bbox": [0, 0, 10, 10],
        "centroid": centroid,
        "zones": ["zone_1"],
        "dwell_seconds": 0.0,
        "restricted_zone_alert": False,
    }


def test_bag_with_nearby_person_no_alert() -> None:
    detector = UnattendedObjectDetector()
    event = _event("2026-01-01T00:00:00+00:00", [_person(1, [100, 100]), _bag(2, [120, 120])])
    assert detector.analyze(event) == []


def test_bag_without_person_below_threshold_no_alert() -> None:
    detector = UnattendedObjectDetector()
    e1 = _event("2026-01-01T00:00:00+00:00", [_bag(2, [300, 300])])
    e2 = _event("2026-01-01T00:00:10+00:00", [_bag(2, [300, 300])])
    detector.analyze(e1)
    assert detector.analyze(e2) == []


def test_bag_without_person_above_threshold_generates_alert() -> None:
    detector = UnattendedObjectDetector()
    e1 = _event("2026-01-01T00:00:00+00:00", [_bag(2, [300, 300])])
    e2 = _event("2026-01-01T00:00:20+00:00", [_bag(2, [300, 300])])
    detector.analyze(e1)
    alerts = detector.analyze(e2)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "unattended_object"


def test_euclidean_distance_helper() -> None:
    assert round(UnattendedObjectDetector.euclidean_distance([0, 0], [3, 4]), 2) == 5.0


def test_reset_when_person_approaches_bag() -> None:
    detector = UnattendedObjectDetector()
    detector.analyze(_event("2026-01-01T00:00:00+00:00", [_bag(2, [300, 300])]))
    detector.analyze(_event("2026-01-01T00:00:05+00:00", [_person(1, [305, 305]), _bag(2, [300, 300])]))
    alerts = detector.analyze(_event("2026-01-01T00:00:25+00:00", [_bag(2, [300, 300])]))
    assert alerts == []
