from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for backend ORM models."""


async def init_db(engine: AsyncEngine) -> None:
    """Create database tables for all registered ORM models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
