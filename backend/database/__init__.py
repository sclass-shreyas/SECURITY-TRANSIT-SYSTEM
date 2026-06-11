from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for backend ORM models."""


async def init_db(engine: AsyncEngine) -> None:
    """Create database tables for all registered ORM models."""
    # Import both schema tracks so their tables are registered on the shared runtime Base.
    from backend import models as _new_models  # noqa: F401
    from backend.models import legacy as _legacy_models  # noqa: F401
    from backend.database.base import Base as NewBase

    metadata_sets = [Base.metadata, NewBase.metadata]

    async with engine.begin() as conn:
        for metadata in metadata_sets:
            await conn.run_sync(metadata.create_all)


def create_engine_and_sessionmaker(database_url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an async SQLAlchemy engine and sessionmaker.

    Args:
        database_url: SQLAlchemy async database URL.

    Returns:
        A tuple containing the async engine and async sessionmaker.
    """
    engine = create_async_engine(database_url, echo=False, future=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, sessionmaker
