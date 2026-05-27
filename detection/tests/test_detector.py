"""Tests for YOLO detector wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from detector import Detector


class _Scalar:
    """Mock scalar tensor-like value with .item()."""

    def __init__(self, value: float) -> None:
        self._value = value

    def item(self) -> float:
        """Return scalar value."""
        return self._value


class _XYXY:
    """Mock xyxy holder with tolist method."""

    def __init__(self, coords: list[float]) -> None:
        self._coords = coords

    def tolist(self) -> list[float]:
        """Return coordinates list."""
        return self._coords


class _Box:
    """Mock YOLO box object."""

    def __init__(self, cls_id: int, conf: float, coords: list[float]) -> None:
        self.cls = _Scalar(cls_id)
        self.conf = _Scalar(conf)
        self.xyxy = [_XYXY(coords)]


def _mock_result(boxes: list[_Box]) -> MagicMock:
    result = MagicMock()
    result.boxes = boxes
    return result


@patch("detector.torch.cuda.is_available", return_value=False)
@patch("detector.YOLO")
def test_detect_returns_required_keys(mock_yolo: MagicMock, _: MagicMock) -> None:
    """detect should return list of dicts with required keys."""
    model = MagicMock()
    model.names = {0: "person"}
    model.predict.return_value = [_mock_result([_Box(0, 0.9, [1, 2, 3, 4])])]
    mock_yolo.return_value = model

    detector = Detector()
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)

    assert len(detections) == 1
    assert set(detections[0].keys()) == {"class_name", "confidence", "bbox"}


@patch("detector.torch.cuda.is_available", return_value=False)
@patch("detector.YOLO")
def test_detect_filters_to_target_classes(mock_yolo: MagicMock, _: MagicMock) -> None:
    """detect should keep only configured target classes."""
    model = MagicMock()
    model.names = {0: "person", 1: "dog"}
    model.predict.return_value = [_mock_result([_Box(0, 0.9, [1, 2, 3, 4]), _Box(1, 0.95, [5, 6, 7, 8])])]
    mock_yolo.return_value = model

    detector = Detector()
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)

    assert len(detections) == 1
    assert detections[0]["class_name"] == "person"


@patch("detector.torch.cuda.is_available", return_value=False)
@patch("detector.YOLO")
def test_detect_applies_confidence_threshold(mock_yolo: MagicMock, _: MagicMock) -> None:
    """detect should drop detections under confidence threshold."""
    model = MagicMock()
    model.names = {0: "person"}
    model.predict.return_value = [_mock_result([_Box(0, 0.1, [1, 2, 3, 4]), _Box(0, 0.9, [9, 10, 11, 12])])]
    mock_yolo.return_value = model

    detector = Detector()
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)

    assert len(detections) == 1
    assert detections[0]["bbox"] == [9, 10, 11, 12]


@patch("detector.torch.cuda.is_available", return_value=False)
@patch("detector.YOLO")
def test_empty_frame_returns_empty_list(mock_yolo: MagicMock, _: MagicMock) -> None:
    """detect should return empty list for empty frame input."""
    model = MagicMock()
    model.names = {0: "person"}
    model.predict.return_value = []
    mock_yolo.return_value = model

    detector = Detector()
    detections = detector.detect(np.empty((0, 0, 3), dtype=np.uint8))

    assert detections == []
