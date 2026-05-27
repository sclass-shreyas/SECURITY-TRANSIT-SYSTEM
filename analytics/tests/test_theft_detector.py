"""Tests for theft gesture detector."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from theft_detector import TheftDetector


class _Landmark:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


def _event() -> dict:
    return {
        "frame_id": 1,
        "objects": [
            {
                "object_id": 1,
                "class_name": "person",
                "confidence": 0.9,
                "bbox": [0, 0, 100, 100],
                "centroid": [50, 50],
                "zones": ["zone_1"],
                "dwell_seconds": 5.0,
                "restricted_zone_alert": False,
            }
        ],
    }


@patch("theft_detector.mp")
def test_empty_frame_returns_empty_list(mock_mp: MagicMock) -> None:
    mock_pose = MagicMock()
    mock_pose.process.return_value = SimpleNamespace(pose_landmarks=None)
    mock_mp.solutions.pose.Pose.return_value = mock_pose

    detector = TheftDetector()
    assert detector.analyze(np.empty((0, 0, 3), dtype=np.uint8), _event()) == []


@patch("theft_detector.mp")
def test_below_threshold_generates_no_alert(mock_mp: MagicMock) -> None:
    mock_pose = MagicMock()
    lm = [_Landmark(0.5, 0.5) for _ in range(40)]
    mock_pose.process.return_value = SimpleNamespace(pose_landmarks=SimpleNamespace(landmark=lm))
    mock_mp.solutions.pose.Pose.return_value = mock_pose
    mock_mp.solutions.pose.PoseLandmark = SimpleNamespace(
        LEFT_WRIST=0, RIGHT_WRIST=1, LEFT_HIP=2, RIGHT_HIP=3
    )

    detector = TheftDetector()
    detector._compute_confidence = MagicMock(return_value=0.2)
    alerts = detector.analyze(np.zeros((100, 100, 3), dtype=np.uint8), _event())
    assert alerts == []


@patch("theft_detector.mp")
def test_above_threshold_generates_alert(mock_mp: MagicMock) -> None:
    mock_pose = MagicMock()
    lm = [_Landmark(0.5, 0.5) for _ in range(40)]
    mock_pose.process.return_value = SimpleNamespace(pose_landmarks=SimpleNamespace(landmark=lm))
    mock_mp.solutions.pose.Pose.return_value = mock_pose
    mock_mp.solutions.pose.PoseLandmark = SimpleNamespace(
        LEFT_WRIST=0, RIGHT_WRIST=1, LEFT_HIP=2, RIGHT_HIP=3
    )

    detector = TheftDetector()
    detector._compute_confidence = MagicMock(return_value=0.9)
    alerts = detector.analyze(np.zeros((100, 100, 3), dtype=np.uint8), _event())
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "theft_gesture"


@patch("theft_detector.mp")
def test_velocity_calculation_non_negative(mock_mp: MagicMock) -> None:
    mock_pose = MagicMock()
    mock_mp.solutions.pose.Pose.return_value = mock_pose

    detector = TheftDetector()
    detector._previous_landmarks[1] = {"timestamp": 1.0, "landmarks": {"wrist": (0.2, 0.2)}}
    confidence = detector._compute_confidence(1, (0.3, 0.3), (0.3, 0.31))
    assert confidence >= 0.0
