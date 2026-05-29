# Technical Debt

## Critical
- No backend ingestion service beyond `mock_server.py`.
- No authentication/authorization for event ingestion.
- No persistence layer for security events.
- No production deployment or containerization.

## High
- No frontend dashboard or visualization beyond OpenCV.
- Event schema and alerting logic are not validated or enforced.
- `config.DEVICE` defaults to `cuda` without fallback configuration when GPU is unavailable.
- The `yolo11n.pt` model file is included but has no version documentation or provenance.

## Medium
- No retries, batching, or backpressure for HTTP event publishing.
- Dwell threshold and unattended threshold values are defined but not applied to event semantics.
- No integration tests for the end-to-end pipeline.
- Hard-coded zone definitions in `zones.json` without administrative API.

## Low
- No `__init__.py` in `detection/`, which limits packaging portability.
- No README or usage documentation at the repository root.
- `mock_server.py` dependencies are not represented in `requirements.txt`.
- No log rotation or structured logging strategy.
