"""Tests for webcam capture utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from capture import FrameCapture


@patch("capture.cv2.VideoCapture")
def test_camera_opens_successfully(mock_video_capture: MagicMock) -> None:
    """FrameCapture should initialize when camera opens."""
    cap_mock = MagicMock()
    cap_mock.isOpened.return_value = True
    mock_video_capture.return_value = cap_mock

    capture = FrameCapture(0, 640, 640)

    assert capture.is_opened() is True


@patch("capture.cv2.resize")
@patch("capture.cv2.VideoCapture")
def test_read_frame_returns_correct_shape(
    mock_video_capture: MagicMock, mock_resize: MagicMock
) -> None:
    """read_frame should return a 640x640x3 frame."""
    input_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    output_frame = np.zeros((640, 640, 3), dtype=np.uint8)

    cap_mock = MagicMock()
    cap_mock.isOpened.return_value = True
    cap_mock.read.return_value = (True, input_frame)
    mock_video_capture.return_value = cap_mock
    mock_resize.return_value = output_frame

    capture = FrameCapture(0, 640, 640)
    success, frame = capture.read_frame()

    assert success is True
    assert frame.shape == (640, 640, 3)


@patch("capture.cv2.VideoCapture")
def test_runtime_error_when_camera_invalid(mock_video_capture: MagicMock) -> None:
    """FrameCapture should raise RuntimeError when camera fails to open."""
    cap_mock = MagicMock()
    cap_mock.isOpened.return_value = False
    mock_video_capture.return_value = cap_mock

    with pytest.raises(RuntimeError):
        FrameCapture(99, 640, 640)


@patch("capture.cv2.VideoCapture")
def test_release_closes_device(mock_video_capture: MagicMock) -> None:
    """release should call underlying capture release."""
    cap_mock = MagicMock()
    cap_mock.isOpened.return_value = True
    mock_video_capture.return_value = cap_mock

    capture = FrameCapture(0, 640, 640)
    capture.release()

    cap_mock.release.assert_called_once()
