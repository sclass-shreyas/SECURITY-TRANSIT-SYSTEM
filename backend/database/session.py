from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_engine_and_sessionmaker(
    database_url: str,
    *,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    pool_recycle: int = 1800,
    echo: bool = False,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    if not database_url.startswith("postgresql+asyncpg"):
        raise ValueError("PostgreSQL is required; set DATABASE_URL to a postgresql+asyncpg URL")

    engine_kwargs: dict[str, object] = {
        "future": True,
        "echo": echo,
        "pool_pre_ping": True,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
        "pool_recycle": pool_recycle,
    }
    engine = create_async_engine(database_url, **engine_kwargs)
    sessionmaker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return engine, sessionmaker


async def ping_database(sessionmaker: async_sessionmaker[AsyncSession]) -> bool:
    from sqlalchemy import text

    async with sessionmaker() as session:
        result = await session.execute(text("SELECT 1"))
        return result.scalar_one() == 1
