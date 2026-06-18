from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import Settings, get_settings
from backend.database import create_engine_and_sessionmaker
from backend import models as _models  # noqa: F401
from backend.routes.clips import router as clips_router
from backend.routes.analytics_results import router as analytics_results_router
from backend.routes.events import (
    ingest_alert,
    ingest_event,
    ingest_frame,
    read_alert,
    read_alerts,
    read_incident,
    read_incidents,
)
from backend.routes.events import router as events_router
from backend.routes.health import router as health_router
from backend.routes.stats import router as stats_router
from backend.routes.zones import router as zones_router
from backend.schemas.alert import AlertOut
from backend.schemas.common import MessageResponse
from backend.services.cameras import ensure_default_camera

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("backend")


def _install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_exception", "detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "validation_error", "detail": "Request validation failed", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled backend exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "internal_server_error", "detail": "Unexpected server error"},
        )


def _install_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = str(uuid4())
        start = time.perf_counter()
        logger.info("request_start id=%s method=%s path=%s", request_id, request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed id=%s method=%s path=%s", request_id, request.method, request.url.path)
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
        logger.info(
            "request_complete id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI backend application."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        clips_dir = Path(settings.CLIPS_BASE_DIR)
        clips_dir.mkdir(parents=True, exist_ok=True)

        engine, sessionmaker = create_engine_and_sessionmaker(settings.DATABASE_URL)
        app.state.settings = settings
        app.state.engine = engine
        app.state.sessionmaker = sessionmaker
        app.state.ready = False

        async with sessionmaker() as session:
            session.info["settings"] = settings
            await ensure_default_camera(session)
        app.state.ready = True
        logger.info("Backend startup complete.")
        try:
            yield
        finally:
            app.state.ready = False
            await engine.dispose()
            logger.info("Backend shutdown complete.")

    app = FastAPI(title=settings.APP_NAME, version=settings.SERVICE_VERSION, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _install_exception_handlers(app)
    _install_middleware(app)

    app.include_router(health_router)
    app.include_router(events_router)
    app.include_router(analytics_results_router)
    app.include_router(zones_router)
    app.include_router(clips_router)
    app.include_router(stats_router)

    @app.get("/", response_class=FileResponse, include_in_schema=False)
    async def serve_dashboard() -> FileResponse:
        """Serve the backend-hosted operations dashboard."""
        return FileResponse(Path(__file__).resolve().parent / "static" / "index.html")

    @app.get("/dashboard", response_class=FileResponse, include_in_schema=False)
    async def serve_dashboard_alias() -> FileResponse:
        """Serve the dashboard from a named alias route."""
        return await serve_dashboard()

    @app.get("/alerts.html", response_class=FileResponse, include_in_schema=False)
    async def serve_alerts_dashboard() -> FileResponse:
        """Serve the alerts dashboard."""
        static_dir = Path(__file__).resolve().parent / "app" / "static"
        alerts_file = static_dir / "alerts.html"
        if not alerts_file.exists():
            raise HTTPException(status_code=404, detail="Alerts dashboard not found")
        return FileResponse(alerts_file, media_type="text/html")

    # Compatibility aliases for the existing detector HTTP publisher.
    app.add_api_route("/events", ingest_event, methods=["POST"], response_model=MessageResponse)
    app.add_api_route("/alerts", ingest_alert, methods=["POST"], response_model=MessageResponse)
    app.add_api_route("/frame", ingest_frame, methods=["POST"], response_model=MessageResponse)
    app.add_api_route("/alerts", read_alerts, methods=["GET"], response_model=list[AlertOut])
    app.add_api_route("/alerts/{alert_id}", read_alert, methods=["GET"], response_model=AlertOut)
    app.add_api_route("/incidents", read_incidents, methods=["GET"], response_model=list[AlertOut])
    app.add_api_route("/incidents/{alert_id}", read_incident, methods=["GET"], response_model=AlertOut)

    return app


app = create_app()
