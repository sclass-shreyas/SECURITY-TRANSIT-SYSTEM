"""Tests for DeepSORT object tracker wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from tracker import ObjectTracker


def _track(
    track_id: int,
    confirmed: bool,
    bbox: list[int],
    class_name: str = "person",
    confidence: float = 0.9,
) -> MagicMock:
    track = MagicMock()
    track.track_id = track_id
    track.is_confirmed.return_value = confirmed
    track.to_ltrb.return_value = bbox
    track.get_det_class.return_value = class_name
    track.get_det_conf.return_value = confidence
    return track


@patch("tracker.DeepSort")
def test_update_returns_tracked_objects_with_object_id(mock_deepsort: MagicMock) -> None:
    """update should return confirmed tracks with object IDs."""
    ds = MagicMock()
    ds.update_tracks.return_value = [_track(1, True, [10, 20, 30, 40])]
    mock_deepsort.return_value = ds

    tracker = ObjectTracker()
    detections = [{"class_name": "person", "confidence": 0.9, "bbox": [10, 20, 30, 40]}]
    frame = np.zeros((640, 640, 3), dtype=np.uint8)

    result = tracker.update(detections, frame)

    assert len(result) == 1
    assert result[0]["object_id"] == 1


@patch("tracker.DeepSort")
def test_empty_detections_returns_empty_list(mock_deepsort: MagicMock) -> None:
    """update should return empty list when no detections are provided."""
    ds = MagicMock()
    mock_deepsort.return_value = ds

    tracker = ObjectTracker()
    frame = np.zeros((640, 640, 3), dtype=np.uint8)

    assert tracker.update([], frame) == []


@patch("tracker.DeepSort")
def test_output_contains_required_keys(mock_deepsort: MagicMock) -> None:
    """Tracked object output must include required schema keys."""
    ds = MagicMock()
    ds.update_tracks.return_value = [_track(7, True, [1, 2, 10, 20], "backpack", 0.85), _track(8, False, [3, 4, 12, 22])]
    mock_deepsort.return_value = ds

    tracker = ObjectTracker()
    detections = [{"class_name": "backpack", "confidence": 0.85, "bbox": [1, 2, 10, 20]}]
    frame = np.zeros((640, 640, 3), dtype=np.uint8)

    result = tracker.update(detections, frame)

    assert len(result) == 1
    assert set(result[0].keys()) == {"object_id", "class_name", "confidence", "bbox"}
