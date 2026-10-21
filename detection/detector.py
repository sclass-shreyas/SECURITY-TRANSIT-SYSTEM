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
        self.is_openvino = False
        self.device = "cpu"

        preferred = getattr(config, "DEVICE", "auto").lower()

        # Check OpenVINO capability
        openvino_gpu_available = False
        openvino_installed = False
        try:
            from openvino.runtime import Core
            core = Core()
            openvino_installed = True
            openvino_gpu_available = any("GPU" in d for d in core.available_devices)
        except Exception:
            pass

        # Resolve target device and engine
        if preferred == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif openvino_gpu_available:
                self.device = "GPU"
                self.is_openvino = True
            elif openvino_installed:
                self.device = "CPU"
                self.is_openvino = True
            else:
                self.device = "cpu"
        elif preferred in ("openvino_gpu", "openvino"):
            if openvino_gpu_available:
                self.device = "GPU"
                self.is_openvino = True
            else:
                self.logger.warning("OpenVINO GPU requested but unavailable. Falling back to OpenVINO CPU.")
                self.device = "CPU"
                self.is_openvino = openvino_installed
        elif preferred == "openvino_cpu":
            self.device = "CPU"
            self.is_openvino = openvino_installed
        elif preferred == "cuda":
            if torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.logger.warning("CUDA unavailable. Falling back to CPU.")
                self.device = "cpu"
        else:
            self.device = "cpu"

        # Model loading (OpenVINO vs PyTorch)
        if self.is_openvino:
            from pathlib import Path
            ov_path = Path(getattr(config, "OPENVINO_DIR", "yolo11n_openvino_model"))
            base_model_path = Path(config.YOLO_MODEL_NAME)

            if not ov_path.exists() and base_model_path.exists():
                self.logger.info("Exporting %s to OpenVINO FP16 format...", base_model_path)
                try:
                    exporter = YOLO(str(base_model_path))
                    exporter.export(format="openvino", half=getattr(config, "HALF_PRECISION", True))
                except Exception as e:
                    self.logger.warning("Failed to export OpenVINO model: %s. Falling back to PyTorch.", e)
                    self.is_openvino = False

            if self.is_openvino and ov_path.exists():
                self.logger.info("Loading OpenVINO model from %s on device: %s", ov_path, self.device)
                self.model = YOLO(str(ov_path), task="detect")
            else:
                self.model = YOLO(config.YOLO_MODEL_NAME)
                self.device = "cpu"
                self.is_openvino = False
        else:
            self.model = YOLO(config.YOLO_MODEL_NAME)
            if hasattr(self.model, "to"):
                self.model.to(self.device)
            if self.device == "cuda" and getattr(config, "HALF_PRECISION", False):
                if hasattr(self.model, "model") and hasattr(self.model.model, "half"):
                    self.model.model.half()
                    self.logger.info("Using CUDA half precision for YOLO inference.")

        self.logger.info("Detector initialized: Engine=%s, Device=%s", "OpenVINO" if self.is_openvino else "PyTorch", self.device)
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
