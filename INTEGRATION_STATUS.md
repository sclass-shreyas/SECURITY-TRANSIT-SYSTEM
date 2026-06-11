# Integration Status

## Current Architecture State

- Backend runtime now defaults to PostgreSQL and resolves `DATABASE_URL` from the environment when provided.
- Alembic is configured through `backend/alembic.ini` and `backend/alembic/env.py` uses the resolved PostgreSQL URL.
- The live backend app starts successfully against PostgreSQL, seeds the default camera and zones, and reports ready.
- Analytics remains operational and can publish events, alerts, and analytics-results to the backend.
- The compatibility `backend.models.legacy` module now re-exports the current ORM models so SQLite-based test flows can share the same schema shape.

## Completed Integrations

1. Detection -> Backend event ingestion
   - `POST /events` and `POST /api/v1/events` accept detection payloads.
   - Event persistence works with both the live backend and the test harness.

2. Analytics -> Backend alert ingestion
   - `POST /alerts` and `POST /api/v1/alerts` accept alert payloads.
   - Alerts now attach to an existing event when the frame matches, or create a synthetic event when no matching event exists.

3. Backend -> PostgreSQL persistence
   - Alembic migration head is applied successfully.
   - Runtime startup inserts the default camera and zone seed rows.
   - Direct SQLAlchemy queries confirm tables and inserted rows in PostgreSQL.

4. Health and readiness
   - `/health` and `/ready` report successful startup and database readiness.

5. Read APIs and stats
   - Alert, zone, clip, analytics-results, and stats read endpoints are operational.

6. Test coverage
   - `backend/tests` passes.
   - `analytics/tests` passes.
   - `detection/tests` passes.

## Migration Status

- `alembic -c backend/alembic.ini current` resolves to `0002_zone_compatibility`.
- `alembic -c backend/alembic.ini history` shows the full chain from `0001_initial` to `0002_zone_compatibility`.
- `alembic -c backend/alembic.ini heads` reports a single head.

## Outstanding Notes

- SQLite remains in the repository for compatibility test paths, but the production runtime path now uses PostgreSQL.
- Firebase notification support remains optional and disabled when credentials are absent.

## Recent Validation Evidence

- Backend startup log: `Backend startup complete.`
- PostgreSQL schema check:
  - `alembic_version = 0002_zone_compatibility`
  - tables present: `cameras`, `zones`, `events`, `alerts`, `clips`, `analytics_results`
- Runtime health:
  - `GET /ready` => `{"status":"ready","ready":true,"database":"ok"}`
- Test suites:
  - `backend/tests`: `7 passed, 1 skipped`
  - `analytics/tests`: `29 passed`
  - `detection/tests`: `20 passed`
