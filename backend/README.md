# Smart Transit Backend (P3)

FastAPI backend for Smart Transit Security Surveillance with SQLite-first, PostgreSQL-ready SQLAlchemy models, JWT auth, REST APIs, and live WebSocket broadcasting.

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
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Default Admin

- username: `admin`
- password: `admin123`

Change values in `.env` using `DEFAULT_ADMIN_USERNAME` and `DEFAULT_ADMIN_PASSWORD`.

## Key Endpoints

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /events`
- `POST /frame`
- `POST /alerts`
- `GET /alerts`
- `GET /alerts/{alert_id}`
- `GET /incidents`
- `GET /incidents/{alert_id}`
- `GET /zones`
- `POST /zones`
- `PUT /zones/{zone_id}`
- `DELETE /zones/{zone_id}`
- `GET /clips/{alert_id}`
- `GET /stats/summary`
- `GET /stats/timeline`
- `GET /health`
- `WS /ws/live`

## Tests

```bash
pytest -q
```
