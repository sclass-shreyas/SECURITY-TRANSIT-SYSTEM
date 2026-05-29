# Project Handoff

## Purpose
This repository contains a real-time smart transit security prototype focused on camera-based object detection, tracking, and zone-based event publishing.

## Scope
The codebase is primarily a detection pipeline and proof-of-concept event ingestion flow. It does not include a production backend, frontend dashboard, or model training pipeline.

## Key Objectives
- Capture video frames from a camera
- Detect transit security-relevant objects using a YOLO model
- Track objects across frames with DeepSORT
- Map objects to pre-defined security zones
- Publish structured events to an HTTP endpoint
- Provide zone overlay visualization via OpenCV

## Repository Structure

### `SECURITY-TRANSIT-SYSTEM/`
- Purpose: top-level project shell and mock backend support.
- Important files:
  - `mock_server.py`: FastAPI stub that receives `/events` POST payloads.
  - `.gitignore`: standard ignore entries.
- Dependencies:
  - `fastapi`, `uvicorn` are implied by `mock_server.py` but not pinned in requirements.

### `SECURITY-TRANSIT-SYSTEM/detection/`
- Purpose: core detection pipeline implementation.
- Important files:
  - `main.py`: orchestrates capture, detection, tracking, zoning, overlay drawing, and event publishing.
  - `capture.py`: webcam frame acquisition and resizing.
  - `detector.py`: YOLO11n-based object detection wrapper.
  - `tracker.py`: DeepSORT object tracking wrapper.
  - `zone_manager.py`: polygon zone membership and dwell-time logic.
  - `event_publisher.py`: asynchronous HTTP event delivery.
  - `config.py`: runtime configuration constants.
  - `zones.json`: hard-coded zone definitions.
- Dependencies:
  - `ultralytics`, `opencv-python`, `deep-sort-realtime`, `numpy`, `httpx`

### `SECURITY-TRANSIT-SYSTEM/detection/tests/`
- Purpose: unit tests for pipeline components.
- Important files:
  - `test_capture.py`, `test_detector.py`, `test_tracker.py`, `test_zone_manager.py`, `test_event_publisher.py`
- Dependencies:
  - `pytest`, `pytest-asyncio`

## Execution Overview

### How to run
1. Activate Python virtual environment.
2. Start the mock API server from the repository root:
   ```powershell
   python mock_server.py
   ```
3. Run the detection loop:
   ```powershell
   python detection/main.py
   ```

### Current implementation status
- Completed:
  - Runtime frame capture
  - YOLO inference wrapper
  - DeepSORT tracking wrapper
  - Zone classification and dwell-time computation
  - Event JSON payload generation and HTTP publishing
  - Unit-level tests for core components
- Partial:
  - Event delivery is best-effort; no retry/backpressure logic.
  - Restricted zone and dwell threshold parameters exist but are not fully operational as alerting rules.
  - Backend is a mock server only; no persistence or query interface.
- Missing:
  - Frontend/dashboard
  - Production API backend and database
  - Authentication/authorization
  - Training dataset and model training pipeline
  - Deployment manifests and CI/CD

## Known Constraints and Assumptions
- The repository is inference-only; no model training code is provided.
- The included model file `yolo11n.pt` is a pre-trained weight bundle and not inspectable.
- The pipeline assumes a local camera and a windowed OpenCV display.
- The API endpoint is configured for `http://localhost:8000/events`; the actual backend service is absent except for `mock_server.py`.

## Notes for Handoff
- The main detection loop is in `detection/main.py`.
- If the detection loop is run from within the `detection/` folder, Python imports work because modules are sibling files.
- If the pipeline is moved into a package, add `__init__.py` and update imports accordingly.
- Validate that the environment has a compatible GPU driver if `config.DEVICE` remains `cuda`.

## Immediate concerns for future engineers
- No backend persistence means events are currently transient and only visible in the mock server output.
- The only UI is an OpenCV window; there is no web-based monitoring or operator console.
- Security is not addressed; the HTTP event API is open and unauthenticated.
