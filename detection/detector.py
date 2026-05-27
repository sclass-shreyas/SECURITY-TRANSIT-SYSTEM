"""YOLO11n detector wrapper for real-time object detection."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import torch
from ultralytics import YOLO

import config


class Detector:
    """Run YOLO11n inference and return normalized detection dictionaries."""

    def __init__(self) -> None:
        """Load model, configure device, and precision settings."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = YOLO(config.YOLO_MODEL_NAME)

        preferred_device = config.DEVICE
        if preferred_device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
            self.logger.warning("CUDA unavailable. Falling back to CPU for inference.")
        else:
            self.device = preferred_device

        self.model.to(self.device)

        if self.device == "cuda" and config.HALF_PRECISION:
            self.model.model.half()
            self.logger.info("Using CUDA half precision for YOLO inference.")

        self.target_classes = set(config.TARGET_CLASSES)

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Run inference and return filtered detections.

        Args:
            frame: Input frame as numpy array.

        Returns:
            Detection dict list with class name, confidence, and xyxy bounding box.
        """
        if frame.size == 0:
            return []

        results = self.model.predict(
            source=frame,
            conf=config.CONFIDENCE_THRESHOLD,
            iou=config.NMS_IOU_THRESHOLD,
            verbose=False,
            device=self.device,
        )

        detections: list[dict[str, Any]] = []
        names = self.model.names
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_index = int(box.cls.item())
                class_name = names.get(cls_index, str(cls_index))
                confidence = float(box.conf.item())
                if class_name not in self.target_classes:
                    continue
                if confidence < config.CONFIDENCE_THRESHOLD:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    {
                        "class_name": class_name,
                        "confidence": confidence,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    }
                )

        return detections
