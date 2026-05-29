# Smart Transit Backend

FastAPI backend for Smart Transit Security Surveillance with PostgreSQL-only SQLAlchemy models, Alembic migrations, REST APIs, and live WebSocket broadcasting.

## Run

1. Start PostgreSQL:

```bash
docker compose up -d postgres
```

The container initializes both `smart_transit` and `smart_transit_test`.

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the backend environment file:

```bash
cp backend/.env.example backend/.env
```

Set `TEST_DATABASE_URL` to the `smart_transit_test` database for migration verification.

4. Run database migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

5. Start the backend:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload
```

## PostgreSQL Defaults

- `DATABASE_URL` must point to PostgreSQL with the `asyncpg` driver.
- Alembic uses the same PostgreSQL URL from `backend/.env`.
- SQLite is not supported.

## Key Endpoints

- `GET /health`
- `GET /ready`
- `POST /api/v1/events`
- `POST /api/v1/alerts`
- `POST /events`
- `POST /alerts`
- `POST /frame`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/{alert_id}`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{alert_id}`
- `GET /zones`
- `POST /zones`
- `PUT /zones/{zone_id}`
- `DELETE /zones/{zone_id}`
- `GET /clips/{alert_id}`
- `GET /stats/summary`
- `GET /stats/timeline`
- `WS /ws/live`

## Tests

```bash
pytest -q
```

## Migration Verification

To verify the schema against PostgreSQL:

```bash
pytest backend/tests/test_migrations_postgresql.py -q
```

The test runs:

1. `alembic upgrade head`
2. `alembic downgrade base`
3. `alembic upgrade head`
