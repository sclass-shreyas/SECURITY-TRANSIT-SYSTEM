import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.auth.security import get_password_hash
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app import models as _models  # noqa: F401
from app.models.user import User
from app.routes.auth import router as auth_router
from app.routes.clips import router as clips_router
from app.routes.events_alerts import router as events_alerts_router
from app.routes.health import router as health_router
from app.routes.stats import router as stats_router
from app.routes.ws import router as ws_router
from app.routes.zones import router as zones_router

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME))
        if result.scalar_one_or_none() is None:
            session.add(
                User(
                    username=settings.DEFAULT_ADMIN_USERNAME,
                    hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                    role="admin",
                )
            )
            await session.commit()
            logger.info("Default admin user created.")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(events_alerts_router)
app.include_router(zones_router)
app.include_router(clips_router)
app.include_router(ws_router)
app.include_router(health_router)
app.include_router(stats_router)
