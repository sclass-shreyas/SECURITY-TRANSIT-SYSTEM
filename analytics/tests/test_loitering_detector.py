"""Tests for loitering detection module."""

from __future__ import annotations

from loitering_detector import LoiteringDetector


def _event(dwell: float, object_id: int = 1) -> dict:
    return {
        "frame_id": 10,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "objects": [
            {
                "object_id": object_id,
                "class_name": "person",
                "confidence": 0.9,
                "bbox": [1, 2, 3, 4],
                "centroid": [2, 3],
                "zones": ["zone_001"],
                "dwell_seconds": dwell,
                "restricted_zone_alert": False,
            }
        ],
    }


def test_object_below_threshold_generates_no_alert() -> None:
    detector = LoiteringDetector()
    assert detector.analyze(_event(10.0)) == []


def test_object_above_threshold_generates_alert() -> None:
    detector = LoiteringDetector()
    alerts = detector.analyze(_event(16.0))
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "loitering"


def test_same_object_does_not_duplicate() -> None:
    detector = LoiteringDetector()
    detector.analyze(_event(16.0, object_id=7))
    alerts = detector.analyze(_event(20.0, object_id=7))
    assert alerts == []


def test_reset_clears_state() -> None:
    detector = LoiteringDetector()
    detector.analyze(_event(16.0, object_id=5))
    detector.reset(5)
    alerts = detector.analyze(_event(16.5, object_id=5))
    assert len(alerts) == 1


def test_alert_contains_required_keys() -> None:
    detector = LoiteringDetector()
    alerts = detector.analyze(_event(20.0))
    assert set(alerts[0].keys()) == {"alert_type", "object_id", "class_name", "zone", "metadata"}
