# Architecture Overview

## Problem Statement
This project aims to detect and track people and transit-related baggage in a camera stream, determine membership in defined security zones, and publish structured event telemetry for further processing.

## System Architecture
The system is a single-process detection pipeline with a lightweight event publishing interface.

### Core components
- `FrameCapture`: camera input and preprocessing
- `Detector`: YOLO11n inference wrapper
- `ObjectTracker`: DeepSORT tracking wrapper
- `ZoneManager`: polygon zone detection and dwell-time tracking
- `EventPublisher`: async HTTP POST to events API
- `main.py`: orchestration loop

### Supporting component
- `mock_server.py`: placeholder HTTP receiver for `/events`

## Component Dependencies
- `main.py` depends on all pipeline modules (`capture`, `detector`, `tracker`, `zone_manager`, `event_publisher`, `config`)
- `detector.py` depends on `ultralytics`, `torch`, and `numpy`
- `tracker.py` depends on `deep_sort_realtime`, `numpy`
- `zone_manager.py` depends on `opencv-python`, `numpy`
- `event_publisher.py` depends on `httpx`

## Data Flow
1. `FrameCapture` reads a camera frame.
2. `Detector` performs object detection on the frame.
3. `ObjectTracker` associates detections with tracked identities.
4. `ZoneManager` resolves centroid membership against configured polygons.
5. `main.py` builds an event payload containing object metadata, dwell times, and restricted-zone flags.
6. `EventPublisher` POSTs the event payload to the configured API endpoint.
7. `main.py` also renders overlay graphics to an OpenCV window.

## Runtime assumptions
- The pipeline is run in an environment with a connected camera.
- GPU inference is preferred but CPU fallback is supported.
- `mock_server.py` is a stub and not a production intake service.
- No persistence or database exists, so analytics are ephemeral.

## Inferred gaps
- No backend service beyond the mock server.
- No data storage, event indexing, or query API.
- No frontend/UI beyond OpenCV frame rendering.
- No training or dataset management.
- No security controls.

## Diagram references
Detailed flow and dependency diagrams have been captured in `docs/PIPELINE_MAP.md`.
