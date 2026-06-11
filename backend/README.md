+# Smart Transit Backend

FastAPI backend for Smart Transit Security Surveillance with PostgreSQL-ready SQLAlchemy models, Alembic migrations, REST APIs, and live WebSocket broadcasting.

## Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy environment file:

```bash
cp .env.example .env
```

3. Run DB migration:

```bash
alembic -c alembic.ini upgrade head
```

4. Start server:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload
```

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
