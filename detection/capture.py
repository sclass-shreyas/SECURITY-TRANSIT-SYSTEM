"""Webcam frame capture utilities for the detection pipeline."""

from __future__ import annotations

import os
from typing import Tuple

import cv2
import numpy as np


class FrameCapture:
    """Capture and preprocess frames from a webcam source."""

    def __init__(self, camera_index: int, width: int, height: int) -> None:
        """Initialize and open a camera capture device.

        Args:
            camera_index: OpenCV camera index.
            width: Target output width.
            height: Target output height.

        Raises:
            RuntimeError: If camera cannot be opened.
        """
        self._width = width
        self._height = height
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        self._capture = cv2.VideoCapture(camera_index, backend)
        if not self._capture.isOpened():
            raise RuntimeError(
                f"Failed to open camera index {camera_index}. "
                "Verify camera availability and permissions."
            )
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read_frame(self) -> Tuple[bool, np.ndarray]:
        """Read and resize one frame.

        Returns:
            Tuple of success flag and resized frame.
        """
        success, frame = self._capture.read()
        if not success or frame is None:
            return False, np.empty((0, 0, 3), dtype=np.uint8)

        if frame.shape[1] == self._width and frame.shape[0] == self._height:
            return True, frame

        resized = cv2.resize(frame, (self._width, self._height))
        return True, resized

    def is_opened(self) -> bool:
        """Return whether the capture device is open."""
        return self._capture.isOpened()

    def release(self) -> None:
        """Release the capture device."""
        self._capture.release()
