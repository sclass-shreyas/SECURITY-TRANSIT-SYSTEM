from backend.routes.clips import router as clips_router
from backend.routes.events import router as events_router
from backend.routes.health import router as health_router
from backend.routes.stats import router as stats_router
from backend.routes.zones import router as zones_router

__all__ = ["clips_router", "events_router", "health_router", "stats_router", "zones_router"]
