# Next Steps

## Immediate Next Tasks

1. Implement backend event ingestion service
   - Description: Replace `mock_server.py` with a real FastAPI backend that persists `/events` payloads to a database and exposes health/status endpoints.
   - Why it matters: The current pipeline has no reliable storage or operational API.
   - Estimated effort: 3-5 days
   - Dependencies: `httpx`, `fastapi`, database driver

2. Add event schema validation and alert rules
   - Description: Validate the detection event payload and implement configurable restricted-zone / dwell alerts.
   - Why it matters: Ensures data quality and converts raw events into actionable security alerts.
   - Estimated effort: 2-3 days
   - Dependencies: backend service, schema library (Pydantic)

3. Add integration tests for pipeline end-to-end
   - Description: Add tests that cover capture->detect->track->zone->publish using mocks/stubs.
   - Why it matters: Verifies the complete event flow and catches regression risks.
   - Estimated effort: 2 days
   - Dependencies: existing pytest setup

4. Document run and deployment instructions
   - Description: Add a root-level `README.md` and update `requirements.txt` with backend dependencies.
   - Why it matters: Improves handoff clarity and onboarding speed.
   - Estimated effort: 1 day
   - Dependencies: audit docs, dependency inventory

## 30-Day Roadmap

- Stabilize the detection pipeline
  - Harden camera loss handling
  - Add CPU/GPU selection and device fallback logic
  - Add configurable logging and environment-based config
- Build a real event ingestion API
  - FastAPI + Pydantic contract
  - SQLite or PostgreSQL persistence
  - health/readiness endpoints
- Add event validation and security alerts
  - restricted zone alerting
  - dwell / unattended detection rules
- Close immediate documentation gaps
  - root README
  - architecture/operational guide

## 60-Day Roadmap

- Build a frontend monitoring dashboard
  - real-time event stream view
  - camera overlay snapshot display
  - alert history and zone analytics
- Add authentication and role-based access
  - API token or OAuth for dashboard and ingestion
- Add deployment automation
  - Dockerfile(s) for detection and backend
  - compose/dev scripts
  - CI pipeline for lint/test/build
- Add system metrics and logging
  - fps/latency monitoring
  - event publish success rate
  - error tracking

## 90-Day Roadmap

- Add model training and dataset pipeline
  - dataset schema, labeling tools, training jobs
  - model evaluation and validation reports
- Add scaling and multi-camera support
  - distributed event ingestion
  - load-balanced backend
  - camera management service
- Add security hardening
  - encrypted transport for events
  - auth for camera pipeline and API
  - input validation and rate limiting
- Transition prototype into production-ready system
  - deployment manifests for Kubernetes or cloud
  - operational runbooks
